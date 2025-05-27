// background.ts

import { isNetflixWatchPage } from "./netflix/netflixUrlTool";

import {
    distributeTaskData,
    getTaskForDomain,
    handleUserTabsBackIn,
    playPauseDispatch,
} from "./backgroundUtil";

import { NetflixViewing, viewingTracker } from "./videoCommon/visits";

import { setupIgnoredDomains } from "./ignoreList";

import { helpDeveloperNoticeMissingNpmRunBuild } from "./developerExperience";
import { captureManager } from "./inputLogger/initInputCapture";

helpDeveloperNoticeMissingNpmRunBuild();

// enable logging file download
(self as any).getLogsFromEvents = () => captureManager.downloadUserEvents();
(self as any).getLogsFromPayloads = () =>
    captureManager.downloadPayloadEvents();
(self as any).showRemainingTime = () => captureManager.showRemainingTime();
(self as any).countPayloadEvents = () => captureManager.showRemainingTime();

// Disabled in favor of the modal
function openOptionsOnClickIcon() {
    // Don't delete this code
    chrome.action.onClicked.addListener(() => {
        chrome.runtime.openOptionsPage();
    });
}

// openOptionsOnClickIcon();

/*
 * Claude says, re: onUpdated:
 *
 * The chrome.tabs.onUpdated event specifically triggers when any tab
 * in the browser undergoes a state change. This event can fire for various reasons:
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
        captureManager.captureIfEnabled({
            type: "ON_UPDATED_COMPLETE",
            data: { tabId, url: tab.url },
            metadata: {
                source: "onUpdated.addListener",
                method: "user_input",
                location: "background.ts",
                timestamp: new Date().toISOString(),
            },
        });

        const task = getTaskForDomain(tab, (youTubeTask) => {
            distributeTaskData(youTubeTask);
        });
        distributeTaskData(task);
    }
});

// Listen for tab switches.
let currentTabId: number;
chrome.tabs.onActivated.addListener((activeInfo) => {
    currentTabId = activeInfo.tabId;
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        if (tab.url) {
            captureManager.captureIfEnabled({
                type: "ON_UPDATED_COMPLETE",
                data: { tabId: currentTabId, url: tab.url },
                metadata: {
                    source: "onActivated.addListener",
                    method: "user_input",
                    location: "background.ts",
                    timestamp: new Date().toISOString(),
                },
            });
            console.log("onActivated - getDomainFromUrl");
            // SO this one is, "I switch from Chrome Tab A to Chrome Tab B".
            // The other one is, "I alt tab back IN to Chrome."
            // But the alt-tab-back-into-Chrome one also fires "onActivated".
            // TODO: Find a way to choose between this one and the onMessage focus listener
            const task = getTaskForDomain(tab, (youTubeTask) => {
                distributeTaskData(youTubeTask);
            });
            distributeTaskData(task);

            // TODO: On tab into a Player page, get player state from storage, package
            // player state into payload for reportWatchPage. Think
            // it just needs to be, "store the active players in an array of tab IDs"
        } else {
            console.warn("Active tab had no url");
        }
    });
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
        (tab.url.includes("wikipedia") || isNetflixWatchPage(tab.url))
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

chrome.runtime.onMessage.addListener(
    (message, sender: chrome.runtime.MessageSender, sendResponse) => {
        /* BTW the sender object has:
            origin: "https://www.youtube.com"
            tab : {active: true, title, url},
            url: "https://www.youtube.com/watch?v=Pt2Pj3JZ9Ow&t=300s"
            * PROBABLY also has the "source" field
        */
        if (message.type !== "player_state_change") {
            return;
        }
        captureManager.captureIfEnabled({
            type: "PLAYER_STATE_CHANGED",
            data: {
                message: {
                    type: message.type,
                    event: message.event,
                },
                sender: {
                    tab: {
                        url: sender.tab?.url,
                    },
                },
            },
            metadata: {
                source: "onMessage.addListener.player_state_change",
                method: "user_input",
                location: "background.ts",
                timestamp: new Date().toISOString(),
            },
        });
        console.log(
            "start of onMessage listener",
            message.event,
            message.source
        );
        /*
         *   This only runs when the user presses play or pauses the video.
         * Hence they're definitely on a page that already loaded
         * somewhere else in the program.
         */
        if (message.event === "user_pressed_play") {
            // FIXME: User is able to press pause, somehow, before .setCurrent is called
            // TODO: On close ... i need one PER watch screen. what if user has 5 videos going?
            playPauseDispatch.notePlayEvent(sender);
        } else if (message.event === "user_pressed_pause") {
            playPauseDispatch.notePauseEvent();
        } else if (message.event === "youtube_autoplay") {
            console.log("[autoplay] youtube");
            // IF trySendPlayEvent, BUT no page event report yet,
            // THEN bundle them.
            playPauseDispatch.noteYouTubeAutoPlayEvent(sender);
        } else if (message.event === "netflix_autoplay") {
            console.log("[autoplay] netflix");
            playPauseDispatch.noteNetflixAutoPlayEvent(sender);
        }
    }
);

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // Netflix content script events
    if (message.source === "netflix_history_recorder") {
        if (message.event === "netflix_media_selected") {
            if (!sender.tab?.id) {
                console.error(
                    "No tab ID available in netflix_media_selected handler"
                );
                return;
            }
            // TODO: Capture input here for tests
            // Create a new instance in this context with the same data
            const partialWatchEntry = {
                url: message.media.url,
                urlId: message.media.videoId,
                showName: message.media.mediaTitle,
                playerState: message.media.playerState,
            };
            const recreatedMedia = new NetflixViewing(
                partialWatchEntry.urlId,
                partialWatchEntry.showName,
                partialWatchEntry.url,
                partialWatchEntry.playerState,
                sender.tab.id
            );
            viewingTracker.setCurrent(recreatedMedia);
            viewingTracker.reportFilledNetflixWatch(recreatedMedia);
            console.log(
                "Background received media state:",
                viewingTracker.currentMedia
            );
        } else if (message.event === "netflix_page_opened") {
            viewingTracker.reportNetflixWatchPage(
                message.media.fullUrl,
                message.media.pageId
            );
        }
        // Other existing message handling...
    }
});

// PROBLEM: Without this code and it's partner code, the user
// can tab back into Chrome, WITHOUT Tab firing off an "Active Tab"
// alert to the server. So the backend sits there saying "Google Chrome"
// until the user (a) changes tabs or (b) changes player state,
// or that's how it was until this code fixed it.
let switchCounter = 0;
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.event !== "window_gained_focus") {
        return;
    }
    /*
        Code runs when user alt tabs into Chrome
    */
    switchCounter++;
    console.log(
        "Chrome gained focus (switched from another app)",
        switchCounter
    );
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const activeTab = tabs[0];
        // Must hinder both window_gained_focus event and onActivated co-occurring
        const tabbingIntoCurrentlyActiveTab = activeTab.id == currentTabId;
        if (activeTab.url && tabbingIntoCurrentlyActiveTab) {
            captureManager.captureIfEnabled({
                type: "ALT_TAB_BACK_IN",
                data: {
                    id: activeTab.id ? activeTab.id : 9000,
                    url: activeTab.url,
                    title: activeTab.title,
                },
                metadata: {
                    source: "window_gained_focus",
                    method: "user_input",
                    location: "background.ts",
                    timestamp: new Date().toISOString(),
                },
            });
            handleUserTabsBackIn(activeTab.url, activeTab);
        } else {
            console.warn("Active tab had no url");
        }
        // activeTab.url, activeTab.title, etc.
    });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "heartbeat") {
        sendResponse({ status: "alive" });
        return true; // Keep the message channel open for async response
    }
});

// runs when you shut a tab
chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
    // Your code to run when a tab is closed
    console.log(`Tab ${tabId} was closed`);
    captureManager.captureIfEnabled({
        type: "TAB_CLOSED",
        data: {
            tabId,
        },
        metadata: {
            source: "onRemoved.addListener",
            method: "user_input",
            location: "background.ts",
            timestamp: new Date().toISOString(),
        },
    });

    // removeInfo contains additional information
    console.log("Window was closed:", removeInfo.isWindowClosing);

    // Perform any cleanup or final operations here
    viewingTracker.endViewing(tabId);
});

chrome.runtime.onInstalled.addListener(() => {
    setupIgnoredDomains();
});
