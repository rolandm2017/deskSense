import { initializedServerApi } from "./api";
import { ignoredDomains, isDomainIgnored } from "./ignoreList";
import { makeNetflixWatchPageId } from "./netflix/netflixUrlTool";
import { getDomainFromUrl } from "./urlTools";
import { viewingTracker, ViewingTracker } from "./videoCommon/visits";
import {
    getYouTubeVideoId,
    handleYouTubeUrl,
    startSecondaryChannelExtractionScript,
} from "./youtube/youtube";

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

    const domain = getDomainFromUrl(tab.url);
    if (domain) {
        const ignored = isDomainIgnored(domain, ignoredDomains.getAll());
        if (ignored) {
            initializedServerApi.reportIgnoredUrl();
            return;
        }
        // TODO: "If Netflix, use regular ReportTabSwitch.
        //  Unless WatchPage, then report NetflixWatchPage"
        const isYouTube = domain.includes("youtube.com");
        if (isYouTube) {
            console.log("[info] on YouTube");
            // Use the dedicated function to handle YouTube URLs
            handleYouTubeUrl(tab, putTabIdIntoPollingList);
            return;
        }
        const isNetflix = domain.includes("netflix.com");
        if (isNetflix) {
            const isNetflixWatch = domain.includes("netflix.com/watch");
            if (isNetflixWatch) {
                // ViewingTracker will handle it via onMessage
                return;
            }
        }
        initializedServerApi.reportTabSwitch(
            domain,
            tab.title ? tab.title : "No title found"
        );
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

    pauseStartTime: Date | undefined;

    tracker: ViewingTracker;

    // gracePeriodDelayInMs: number;

    constructor(tracker: ViewingTracker) {
        this.playCount = 0;
        this.pauseCount = 0;
        this.pauseStartTime = undefined;
        this.tracker = tracker;
    }

    notePlayEvent(sender: chrome.runtime.MessageSender) {
        this.playCount++;

        console.log("[play event] ", this.tracker.currentMedia);
        if (this.tracker.currentMedia) {
            this.tracker.markPlaying();
            return;
        } else {
            console.warn("ShouldntBeAbleToGetHereError");
            // NOTE that the user LIKELY refreshed the page to get here.
            // It wasn't there yet because, the, the channel extractor
            // script didn't run yet but the "report playing video" code did.
            const isYouTube = "TODO";
            console.log(this.tracker.currentMedia, "207ru");

            throw new Error("ShouldntBeAbleToGetHereError");
            if (isYouTube) {
                // FIXME: THIS RAN ON NETFLIX
                startSecondaryChannelExtractionScript(sender);
                // After the channel extractor runs, then you can fwd the play event
            } else {
                // is netflix
            }
        }
    }

    pageAlreadyReported(senderVideoId: string) {
        // this.mostRecentPageReport = this.currentMedia
        return this.tracker.mostRecentReport?.videoId === senderVideoId;
    }

    pageNotYetLoaded() {
        return this.tracker.currentMedia === undefined;
    }

    noteYouTubeAutoPlayEvent(sender: chrome.runtime.MessageSender) {
        if (this.pageNotYetLoaded()) {
            // wait for the page event to go out, attach "playing" to it
            this.tracker.markAutoplayEventWaiting();
        }
        // https://www.youtube.com/watch?v=Pt2Pj3JZ9Ow&t=300s exists on sender obj
        console.log(sender, "205ru");
        const senderVideoId = getYouTubeVideoId(sender.tab?.url);
        const pageEventAlreadyReported =
            this.pageAlreadyReported(senderVideoId);
        if (pageEventAlreadyReported) {
            this.tracker.markPlaying();
            this.tracker.mostRecentReport = undefined;
        }
    }

    noteNetflixAutoPlayEvent(sender: chrome.runtime.MessageSender) {
        if (this.pageNotYetLoaded()) {
            // wait for the page event to go out, attach "playing" to it
            this.tracker.markAutoplayEventWaiting();
        }
        // https://www.youtube.com/watch?v=Pt2Pj3JZ9Ow&t=300s exists on sender obj
        console.log(sender, "226ru");
        let senderVideoId;
        if (!sender.tab || !sender.tab.url) {
            console.warn(
                "Chrome had a missing 'tab' or 'tab.url' property in MessageSender: ",
                sender.tab
            );
            senderVideoId = "Unknown Video ID";
        } else {
            senderVideoId = makeNetflixWatchPageId(sender.tab?.url);
        }

        const pageEventAlreadyReported =
            this.pageAlreadyReported(senderVideoId);
        if (pageEventAlreadyReported) {
            this.tracker.markPlaying();
            this.tracker.mostRecentReport = undefined;
        }
    }

    notePauseEvent() {
        this.pauseCount++;

        console.log("[pause] ", this.tracker.currentMedia);
        if (this.tracker.currentMedia) {
            this.tracker.markPaused();
        } else {
            console.log(this.tracker.currentMedia, "238ru");
            console.warn("Somehow paused the media while it was undefined");
            throw new Error("ShouldntBeAbleToGetHereError");
        }
    }

    /* NOTE that a grace period before the pause event is set
    yields complexities: What if the user pauses, alt tabs into VSCode a second later?
    
    The Alt Tab into VSCode yields a Program state, but then the pause countdown 
    finishes, the pause event is sent, and now the Program state is bumped off by
    an erroneous Chrome x YouTube state.
    
    It would work if a new Program state or a new Tab state superceded any incoming
    Chrome x YouTube pause event. Like, "Blocked it from entering." But that adds
    complexity. Unnecessary complexity.

    Further, it's a PITA to develop while waiting 3 sec to see your Pause event register.
    */
}

export const playPauseDispatch = new PlayPauseDispatch(viewingTracker);
