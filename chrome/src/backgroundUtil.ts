import { api } from "./api";
import { ignoredDomains, isDomainIgnored } from "./ignoreList";
import { getDomainFromUrl } from "./urlTools";
import { viewingTracker, ViewingTracker } from "./videoCommon/visits";
import { handleYouTubeUrl } from "./youtube/youtube";

import { systemInputCapture } from "./inputLogger/systemInputLogger";

export const tabsWithPollingList: number[] = [];

function putTabIdIntoPollingList(tabId: number) {
    tabsWithPollingList.push(tabId);
}

export function getDomainFromUrlAndSubmit(tab: chrome.tabs.Tab) {
    /*

    This function has a debounce timer barring entry into it.
    Prior to the existence of the debounce, the function would
    gather info about a newly created tab, or a tab that was
    just switched to, two times or I think even four times.
    So the debounce was added to prevent the same tab that was
    just created being gathered multiple times.

    Note, it might be a problem if the user switches back and forth quickly.

    */

    if (!tab.url) {
        console.error("No url found");
        return;
    }

    // Use tab ID-based debouncing if we have a tab ID
    if (!tab.id) {
        throw new Error("A tab had no ID");
    }

    // Check if this tab with this URL was processed recently
    const recentlySeenTab = debounce.isTabBeingProcessed(tab);
    if (recentlySeenTab) {
        // FIXME: What to do when the user visits the same URL 2-3x on multiple tabs?
        return;
    }
    console.log("Tab.url and ID", tab.url, tab.id);

    // no-op if recording disabled
    systemInputCapture.captureIfEnabled({
        type: "TAB_CHANGE",
        data: {
            tabUrl: tab.url,
        },
        metadata: {
            source: "getDomainFromUrlAndSubmit",
            method: "user_input",
            location: "background.ts",
            timestamp: new Date().toISOString(),
        },
    });
    const domain = getDomainFromUrl(tab.url);
    if (domain) {
        const ignored = isDomainIgnored(domain, ignoredDomains.getAll());
        if (ignored) {
            api.reportIgnoredUrl();
            return;
        }
        const isYouTube = domain.includes("youtube.com");
        if (isYouTube) {
            console.log("[info] on YouTube");
            // Use the dedicated function to handle YouTube URLs
            handleYouTubeUrl(tab, putTabIdIntoPollingList);
            return;
        }
        api.reportTabSwitch(domain, tab.title ? tab.title : "No title found");
    } else {
        console.log("No domain found for ", tab.url);
    }
}

interface ProcessedUrlEntry {
    timestamp: number;
    url: string;
}

const PAGE_LOAD_DEBOUNCE_DELAY = 4000;

class DebounceTimer {
    processedTabs: Map<number, ProcessedUrlEntry>;
    constructor() {
        this.processedTabs = new Map<number, ProcessedUrlEntry>();
    }

    isTabBeingProcessed(tab: chrome.tabs.Tab) {
        if (!tab.id) {
            throw new Error("A tab had no ID");
        }
        if (!tab.url) {
            throw new Error("No url found");
        }

        const now = Date.now();

        const lastProcessedTab = this.processedTabs.get(tab.id);
        const tabExistsInMap =
            lastProcessedTab && lastProcessedTab.url === tab.url;

        if (tabExistsInMap) {
            // must use a nested if here because otherwise TS complains re: undefined
            const tabWasSeenRecently =
                now - lastProcessedTab.timestamp < PAGE_LOAD_DEBOUNCE_DELAY;
            if (tabWasSeenRecently) {
                return true;
            }
        }

        // Mark this URL as processed for this tab
        this.processedTabs.set(tab.id, {
            timestamp: now,
            url: tab.url,
        });

        // Clean up old entries periodically
        // 12 chosen because it seems to only happen on youtube and refreshed pages
        if (this.processedTabs.size > 12) {
            this.cleanupOldTabReferences(now);
        }
        return false;
    }

    cleanupOldTabReferences(now: number) {
        // "Now" from new Date().now()
        const tabsToDelete: number[] = [];
        for (const [tabKey, entry] of this.processedTabs.entries()) {
            if (now - entry.timestamp > 10000) {
                // Remove entries older than 10 seconds
                tabsToDelete.push(tabKey);
            }
        }
        tabsToDelete.forEach((key) => this.processedTabs.delete(key));
    }
}

export const debounce = new DebounceTimer();

export class PlayPauseDispatch {
    // TODO: This will have to exist one per video page
    playCount: number;
    pauseCount: number;
    endSessionTimeoutId: ReturnType<typeof setTimeout> | undefined;

    pauseStartTime: Date | undefined;

    tracker: ViewingTracker;

    gracePeriodDelayInMs: number;

    constructor(tracker: ViewingTracker) {
        this.playCount = 0;
        this.pauseCount = 0;
        this.endSessionTimeoutId = undefined;
        this.pauseStartTime = undefined;
        this.tracker = tracker;
        this.gracePeriodDelayInMs = 3000;
    }

    notePlayEvent(sender: chrome.runtime.MessageSender) {
        this.playCount++;
        systemInputCapture.captureIfEnabled({
            type: "PLAY_EVENT",
            data: {},
            metadata: {
                source: "notePlayEvent",
                method: "user_input",
                location: "background.ts",
                timestamp: new Date().toISOString(),
            },
        });
        if (this.endSessionTimeoutId) {
            this.cancelSendPauseEvent(this.endSessionTimeoutId);
        }
        console.log("[play] ", this.tracker.currentMedia);
        if (this.tracker.currentMedia) {
            this.tracker.markPlaying();
            return;
        }
        // else {
        //     // it wasn't there yet because, the, the channel extractor
        //     // script didn't run yet but the "report playing video" code did
        //     // FIXME: THIS RAN ON NETFLIX
        //     startSecondaryChannelExtractionScript(sender);
        // }
    }

    notePauseEvent() {
        this.pauseCount++;
        // no-op if recording disabled
        systemInputCapture.captureIfEnabled({
            type: "PAUSE_EVENT",
            data: {},
            metadata: {
                source: "notePauseEvent",
                method: "user_input",
                location: "background.ts",
                timestamp: new Date().toISOString(),
            },
        });

        console.log("[pause] ", this.tracker.currentMedia);
        if (this.tracker.currentMedia) {
            const startOfGracePeriod = new Date();
            this.pauseStartTime = startOfGracePeriod;

            this.endSessionTimeoutId =
                this.startGracePeriod(startOfGracePeriod);
        }
    }

    startGracePeriod(localTime: Date): ReturnType<typeof setTimeout> {
        // User presses pause, and then resumes the video after only 2.9 seconds, then
        // don't bother pausing tracking.
        const timeoutId = setTimeout(() => {
            if (this.tracker.currentMedia) {
                this.tracker.markPaused();
            }
        }, this.gracePeriodDelayInMs);
        return timeoutId;
    }

    cancelSendPauseEvent(timeoutId: ReturnType<typeof setTimeout>) {
        clearTimeout(timeoutId);
    }
}

export const playPauseDispatch = new PlayPauseDispatch(viewingTracker);
