// background.ts
import { api } from "./api";
import { getDomainFromUrl } from "./urlTools";
import {
    handleYouTubeUrl,
    startSecondaryChannelExtractionScript,
} from "./youtube/youtube";

import { viewingTracker } from "./videoCommon/visits";

import {
    ignoredDomains,
    isDomainIgnored,
    setupIgnoredDomains,
} from "./ignoreList";
import { systemInputCapture } from "./inputLogger/systemInputLogger";

/*

YouTube code, a lot of it lives here, because YouTube is monitored
from the background.ts script itself. 
This approach cannot work for Netflix. Much user input is needed there.

*/

// Code that lets you open the options page when the icon is clicked
// Disabled in favor of the modal
function openOptionsOnClickIcon() {
    // Don't delete this code
    chrome.action.onClicked.addListener(() => {
        chrome.runtime.openOptionsPage();
    });
}

// openOptionsOnClickIcon();

const tabsWithPollingList: number[] = [];

function putTabIdIntoPollingList(tabId: number) {
    tabsWithPollingList.push(tabId);
}

interface ProcessedUrlEntry {
    timestamp: number;
    url: string;
}

// FIXME: What to do when the user visits the same URL 2-3x on multiple tabs?
const processedTabs = new Map<number, ProcessedUrlEntry>();

const PAGE_LOAD_DEBOUNCE_DELAY = 4000;

// TODO: Make debounce stuff a class

function cleanupOldTabReferences(now: number) {
    // "Now" from new Date().now()
    const tabsToDelete: number[] = [];
    for (const [tabKey, entry] of processedTabs.entries()) {
        if (now - entry.timestamp > 10000) {
            // Remove entries older than 10 seconds
            tabsToDelete.push(tabKey);
        }
    }
    tabsToDelete.forEach((key) => processedTabs.delete(key));
}

function markTabProcessed() {
    //
}

function getDomainFromUrlAndSubmit(tab: chrome.tabs.Tab) {
    /*

    This function has a debounce timer barring entry into it.
    Prior to the existence of the debounce, the function would
    gather info about a newly created tab, or a tab that was
    just switched to, two times or I think even four times.
    So the debounce was added to prevent the same tab that was
    just created being gathered multiple times.

    Note, it might be a problem if the user switches back and forth quickly.

    */
    console.log("Tab.url and ID", tab.url, tab.id);

    if (!tab.url) {
        console.error("No url found");
        return;
    }

    const now = Date.now();

    // Use tab ID-based debouncing if we have a tab ID
    if (!tab.id) {
        throw Error("A tab had no ID");
    }

    // Check if this tab with this URL was processed recently
    const lastProcessedTab = processedTabs.get(tab.id);
    const currentTabWasRecentlyProcessed =
        lastProcessedTab && lastProcessedTab.url === tab.url;

    if (currentTabWasRecentlyProcessed) {
        // must use a nested if here because otherwise TS complains re: undefined
        const tabWasSeenRecently =
            now - lastProcessedTab.timestamp < PAGE_LOAD_DEBOUNCE_DELAY;
        if (tabWasSeenRecently) {
            console.log(
                "Skipping recently processed URL:",
                tab.url,
                "in tab:",
                tab.id
            );
            return;
        }
    }

    // Mark this URL as processed for this tab
    processedTabs.set(tab.id, {
        timestamp: now,
        url: tab.url,
    });

    // Clean up old entries periodically
    // 12 chosen because it seems to only happen on youtube and refreshed pages
    if (processedTabs.size > 12) {
        cleanupOldTabReferences(now);
    }

    systemInputCapture.capture({
        type: "TAB_CHANGE",
        data: {
            tabUrl: tab.url,
        },
        metadata: {
            source: "getDomainFromUrlAndSubmit",
            method: "user_input",
            location: "background.ts",
            timestamp: Date.now(),
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

// New tab created
// DISABLED May 9. Not sure it needs to run!
// chrome.tabs.onCreated.addListener((tab) => {
//     if (tab.url) {
//         getDomainFromUrlAndSubmit(tab);
//     }
// });

// runs when you shut a tab
chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
    // Your code to run when a tab is closed
    console.log(`Tab ${tabId} was closed`);
    systemInputCapture.capture({
        type: "TAB_CLOSURE",
        data: { tabId },
        metadata: {
            source: "onRemoved.addListener",
            method: "user_input",
            location: "background.ts",
            timestamp: Date.now(),
        },
    });

    // removeInfo contains additional information
    console.log("Window was closed:", removeInfo.isWindowClosing);

    const isYouTubeWatchPage = tabsWithPollingList.includes(tabId);

    // Perform any cleanup or final operations here
    if (isYouTubeWatchPage && viewingTracker.currentMedia) {
        // send final data to server
        // TODO: This actually ends THE VISIT because a visit is the time on a page!
        // The Viewing would be when the user hits Pause.
        viewingTracker.endViewing();
    }
});

class PlayPauseDispatch {
    // TODO: This will have to exist one per video page
    playCount: number;
    pauseCount: number;
    endSessionTimeoutId: ReturnType<typeof setTimeout> | undefined;

    pauseStartTime: Date | undefined;

    constructor() {
        this.playCount = 0;
        this.pauseCount = 0;
        this.endSessionTimeoutId = undefined;
        this.pauseStartTime = undefined;
    }

    notePlayEvent(sender: chrome.runtime.MessageSender) {
        this.playCount++;
        systemInputCapture.capture({
            type: "PLAY_EVENT",
            data: {},
            metadata: {
                source: "notePlayEvent",
                method: "user_input",
                location: "background.ts",
                timestamp: Date.now(),
            },
        });
        if (this.endSessionTimeoutId) {
            const resumeDuration =
                (new Date().getTime() - this.pauseStartTime!.getTime()) / 1000;
            this.cancelSendPauseEvent(this.endSessionTimeoutId);
        }
        if (viewingTracker.currentMedia) {
            viewingTracker.markPlaying();
            return;
        } else {
            // it wasn't there yet because, the, the channel extractor
            // script didn't run yet but the "report playing video" code did
            startSecondaryChannelExtractionScript(sender);
        }
    }

    notePauseEvent() {
        this.pauseCount++;
        systemInputCapture.capture({
            type: "PAUSE_EVENT",
            data: {},
            metadata: {
                source: "notePauseEvent",
                method: "user_input",
                location: "background.ts",
                timestamp: Date.now(),
            },
        });

        if (viewingTracker.currentMedia) {
            const startOfGracePeriod = new Date();
            this.pauseStartTime = startOfGracePeriod;

            this.endSessionTimeoutId =
                this.startGracePeriod(startOfGracePeriod);
        }
    }

    gracePeriodDelayInMs = 3000;

    startGracePeriod(localTime: Date): ReturnType<typeof setTimeout> {
        // User presses pause, and then resumes the video after only 2.9 seconds, then
        // don't bother pausing tracking.
        const timeoutId = setTimeout(() => {
            const endOfIntervalTime = new Date();
            if (viewingTracker.currentMedia) {
                viewingTracker.markPaused();
            }
        }, this.gracePeriodDelayInMs);
        return timeoutId;
    }

    cancelSendPauseEvent(timeoutId: ReturnType<typeof setTimeout>) {
        clearTimeout(timeoutId);
    }
}

const playPauseDispatch = new PlayPauseDispatch();

chrome.runtime.onMessage.addListener(
    (message, sender: chrome.runtime.MessageSender, sendResponse) => {
        console.log(message, sender);
        /*
         *   This only runs when the user presses play or pauses the video.
         * Hence they're definitely on a page that already loaded
         * somewhere else in the program.
         */
        if (message.event === "user_pressed_play") {
            // TODO: On close ... oh, i need one PER watch screen. what if user has 5 videos going?
            playPauseDispatch.notePlayEvent(sender);
        } else if (message.event === "user_pressed_pause") {
            playPauseDispatch.notePauseEvent();
        } else {
            console.warn("Unknown event:", message);
        }
    }
);

/*
 * Claude says, re: onUpdated:
 *
 * The chrome.tabs.onUpdated event specifically triggers when any tab in the browser undergoes a state change. This event can fire for various reasons:
 *
 * When a page is loading
 * When a page completes loading
 * When a tab's URL changes
 * When a tab's title changes
 * When a tab's favicon changes
 * When a tab's loading status changes
 */

// Listen for any tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    // Chrome's onUpdated event can indeed fire multiple times for a single user action like a refresh
    if (changeInfo.status === "complete" && tab.url) {
        console.log("onUpdated - getDomainFromUrl");
        getDomainFromUrlAndSubmit(tab);
    }
});

// Listen for tab switches.
chrome.tabs.onActivated.addListener((activeInfo) => {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        if (tab.url) {
            console.log("onActivated - getDomainFromUrl");
            getDomainFromUrlAndSubmit(tab);
        }
    });
});

chrome.runtime.onInstalled.addListener(() => {
    setupIgnoredDomains();
});

/*
 * Open the Netflix Watch modal when you click the icon on the right page
 */

chrome.action.onClicked.addListener(async (tab) => {
    console.log("Action.Onclick: ");
    // First check if we're on any Netflix page
    if (
        tab.id &&
        tab.url &&
        (tab.url.includes("wikipedia") || tab.url.includes("netflix.com/watch"))
    ) {
        // Inject the content script
        await chrome.tabs.sendMessage(tab.id, { action: "openModal" });

        // If your script needs to know it was triggered by the icon click,
        // you can pass a message after injection
        // chrome.tabs.sendMessage(tab.id, { action: "extensionIconClicked" });
    } else {
        // Optionally, show a notification or take other action
        console.log(
            "Not on Netflix - script not injected. Tab ID was: ",
            tab.id
        );
    }
});

/*
 * Open the Netflix Watch modal when you click the icon on the right page
 */

chrome.action.onClicked.addListener(async (tab) => {
    console.log("Action.Onclick: ");
    // First check if we're on any Netflix page
    if (
        tab.id &&
        tab.url &&
        (tab.url.includes("wikipedia") || tab.url.includes("netflix.com/watch"))
    ) {
        // Inject the content script
        await chrome.tabs.sendMessage(tab.id, { action: "openModal" });

        // If your script needs to know it was triggered by the icon click,
        // you can pass a message after injection
        // chrome.tabs.sendMessage(tab.id, { action: "extensionIconClicked" });
    } else {
        // Optionally, show a notification or take other action
        console.log(
            "Not on Netflix - script not injected. Tab ID was: ",
            tab.id
        );
    }
});
