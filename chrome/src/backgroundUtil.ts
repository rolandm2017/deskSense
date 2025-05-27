import { initializedServerApi, ServerApi } from "./api";
import {
    isRegularDomainTask,
    isYouTubeHomeTask,
    isYouTubeShortsTask,
    isYouTubeWatchPageTask,
    taskTypes,
} from "./const";
import { MissingMediaError } from "./errors";
import { ignoredDomains, isDomainIgnored } from "./ignoreList";
import { Task } from "./interface/interfaces";
import {
    isNetflixWatchPage,
    makeNetflixWatchPageId,
} from "./netflix/netflixUrlTool";
import { getDomainFromUrl } from "./urlTools";
import { viewingTracker, ViewingTracker } from "./videoCommon/visits";
import {
    getYouTubeVideoId,
    handleYouTubeUrl,
    isWatchingYouTubeVideo,
} from "./youtube/youtube";

export function getTaskForDomain(
    tab: chrome.tabs.Tab,
    extractionDone: (task: Task) => void,
    tracker: ViewingTracker = viewingTracker
): Task | undefined {
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
        throw new Error("A tab had no URL");
    }

    // Use tab ID-based debouncing if we have a tab ID
    if (!tab.id) {
        throw new Error("A tab had no ID");
    }

    // Check if this tab with this URL was processed recently
    // const recentlySeenTab = debounce.isTabBeingProcessed(tab);
    // if (recentlySeenTab) {
    //
    //     console.log("INFO: Debounce saw tab " + tab.id + " recently");
    //     return;
    // }

    const domain = getDomainFromUrl(tab.url);
    if (domain) {
        const ignored = isDomainIgnored(domain, ignoredDomains.getAll());
        if (ignored) {
            // initializedServerApi.reportIgnoredUrl();
            return { type: taskTypes.IGNORED_URL };
        }
        const isYouTube = domain.includes("youtube.com");
        if (isYouTube) {
            console.log("[info] on YouTube");
            // Use the dedicated function to handle YouTube URLs
            // return handleYouTubeUrl(tab);

            const syncTask = handleYouTubeUrl(
                tab,
                (asyncTask) => {
                    // Handle async YouTube watch case
                    extractionDone(asyncTask);
                },
                tracker
            );

            if (syncTask) {
                // Handle all other sync cases
                return syncTask;
            }
        }
        const isNetflix = domain.includes("netflix.com");
        const isNetflixWatch = isNetflixWatchPage(tab.url);
        if (isNetflix && isNetflixWatch) {
            // ViewingTracker will handle it via onMessage
            return { type: taskTypes.NETFLIX_WATCH_PAGE };
        }
        return {
            type: taskTypes.REGULAR_DOMAIN,
            data: {
                domain,
                tabTitle: tab.title ? tab.title : "No title found",
            },
        };
        // initializedServerApi.reportTabSwitch();
    } else {
        console.log("No domain found for ", tab.url);
        return {
            type: taskTypes.ERROR,
        };
    }
}

export function distributeTaskData(
    task: Task | undefined,
    server: ServerApi = initializedServerApi,
    tracker: ViewingTracker = viewingTracker
) {
    // One big switch statement
    if (task === undefined) {
        return;
    } else if (isRegularDomainTask(task)) {
        server.reportTabSwitch(task.data.domain, task.data.tabTitle);
    } else if (task.type === taskTypes.IGNORED_URL) {
        server.reportIgnoredUrl();
    } else if (task.type === taskTypes.NETFLIX_WATCH_PAGE) {
        // do nothing
    } else if (isYouTubeWatchPageTask(task)) {
        tracker.setCurrent(task.data);
        tracker.reportYouTubeWatchPage();
    } else if (isYouTubeShortsTask(task) || isYouTubeHomeTask(task)) {
        server.reportTabSwitch(task.data.domain, task.data.tabTitle);
    } else {
        console.log("Unhandled task type: ", task);
    }
}

export function handleUserTabsBackIn(
    url: string,
    activeTab: chrome.tabs.Tab,
    tracker: ViewingTracker = viewingTracker
) {
    // Default to singleton for prod) {
    /*
        For the case where the user is using some other 
        program, ALT-TABS (emphasis, alt tabs only) back into Chrome.
    */
    if (isWatchingYouTubeVideo(url) || isNetflixWatchPage(url)) {
        console.log("onFocusChanged - a Watch Page");
        if (activeTab.id === undefined) {
            // TODO: Handle by getting it from scratch as if on the page for the first time
            return;
        }
        // If YouTube Watch Page, do special version with player state
        if (!tracker.hasPlayerStateForTab(activeTab.id)) {
            throw new MissingMediaError(
                "latestActiveViewing undefined when tabbing back in"
            );
        }
        /*
        TODO: write the code that handles the user tabbing back in.
                - It only has to do so on Watch Pages
        TODO: Write a nice integration test for this "user tabs back in" scenario

        TODO: Write user input capture. 
                - Capture you watching YouTube.
                    * It must also include you tabbing to other Chrome tabs.
                    * I think it also needs to be aware of you alt tabbing out of Chrome.
                - Capture the API events from this session.
                - Play the events back to the program, expect the same results.


        */
        tracker.handleAltTabReturn(activeTab);
    } else {
        // If Netflix Watch Page, do special version with player state
        // TODO: Could do like, "if returning to page, use stored page/player info".
        // You wouldn't have to store too many values for the page to
        // reliably be among them.
        // else:
        console.log("onFocusChanged - getDomainFromUrl");

        const task = getTaskForDomain(activeTab, (youTubeTask) => {
            distributeTaskData(youTubeTask);
        });
        distributeTaskData(task);
    }
}

interface ProcessedUrlEntry {
    timestamp: number;
    url: string;
}

const PAGE_LOAD_DEBOUNCE_DELAY_IN_MS = 4000;

class DebounceTimer {
    /**
     * Why does this exist?
     *
     */
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
                now - lastProcessedTab.timestamp <
                PAGE_LOAD_DEBOUNCE_DELAY_IN_MS;
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

        console.log("[play event] ", this.tracker.currentMedia?.mediaTitle);
        if (this.tracker.currentMedia) {
            this.tracker.markPlaying();
            return;
        } else {
            // NOTE that the user LIKELY refreshed the page to get here.
            // It wasn't there yet because, the, the channel extractor
            // script didn't run yet but the "report playing video" code did.
            return;
            throw new Error("ShouldntBeAbleToGetHereError");
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
        // Autoplay is when you open a page or refresh, and, the player
        // starts playing automatically.
        if (this.pageNotYetLoaded()) {
            // wait for the page event to go out, attach "playing" to it
            this.tracker.markAutoplayEventWaiting();
        }
        // https://www.youtube.com/watch?v=Pt2Pj3JZ9Ow&t=300s exists on sender obj
        const senderVideoId = getYouTubeVideoId(sender.tab?.url);
        const pageEventAlreadyReported =
            this.pageAlreadyReported(senderVideoId);
        if (pageEventAlreadyReported) {
            this.tracker.markPlaying();
            this.tracker.mostRecentReport = undefined;
        }
    }

    noteNetflixAutoPlayEvent(sender: chrome.runtime.MessageSender) {
        // Autoplay is when you open a page or refresh, and, the player
        // starts playing automatically.
        if (this.pageNotYetLoaded()) {
            // wait for the page event to go out, attach "playing" to it
            this.tracker.markAutoplayEventWaiting();
        }
        // https://www.youtube.com/watch?v=Pt2Pj3JZ9Ow&t=300s exists on sender obj
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

        console.log("[pause] ", this.tracker.currentMedia?.mediaTitle);
        if (this.tracker.currentMedia) {
            this.tracker.markPaused();
        } else {
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
