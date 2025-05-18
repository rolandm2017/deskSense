// background.ts

import {
    getDomainFromUrlAndSubmit,
    playPauseDispatch,
    tabsWithPollingList,
} from "./backgroundUtil";

import { NetflixViewing, viewingTracker } from "./videoCommon/visits";

import {
    clearEndpointLoggingStorage,
    endpointLoggingDownload,
} from "./endpointLogging";
import { setupIgnoredDomains } from "./ignoreList";
import { systemInputCapture } from "./inputLogger/systemInputLogger";

import { captureManager } from "./inputLogger/initInputCapture";

function deskSenseLogs() {
    systemInputCapture.writeLogsToJson();
    endpointLoggingDownload();
}

function clearDeskSenseLogs() {
    systemInputCapture.clearStorage();
    clearEndpointLoggingStorage();
}

function checkIfCaptureSessionStarted() {
    captureManager.getTestStartTime();
}

// enable logging file download
(self as any).deskSenseLogs = deskSenseLogs;
(self as any).clearDeskSenseLogs = clearDeskSenseLogs;
(self as any).deskSenseCaptureCheck = checkIfCaptureSessionStarted;
(self as any).writeInputLogsToJson = systemInputCapture.writeLogsToJson;
(self as any).writeEndpointLogsToJson = endpointLoggingDownload;
// Code that lets you open the options page when the icon is clicked
// Disabled in favor of the modal
function openOptionsOnClickIcon() {
    // Don't delete this code
    chrome.action.onClicked.addListener(() => {
        chrome.runtime.openOptionsPage();
    });
}

// openOptionsOnClickIcon();

// const captureManager = new InputCaptureManager(systemInputCapture, api);
// Periodically check if a recording session has started
// function runCheckOnRecordingSessionStart() {
//     //
//     captureManager.startPolling();
// }

// runCheckOnRecordingSessionStart();

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
    systemInputCapture.captureIfEnabled({
        type: "TAB_CLOSURE",
        data: { tabId },
        metadata: {
            source: "onRemoved.addListener",
            method: "user_input",
            location: "background.ts",
            timestamp: new Date().toISOString(),
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

chrome.runtime.onMessage.addListener(
    (message, sender: chrome.runtime.MessageSender, sendResponse) => {
        console.log(message.event, sender);
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

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.event === "netflix_media_selected") {
        // Create a new instance in this context with the same data
        const partialWatchEntry = {
            urlId: message.media.videoId,
            showName: message.media.mediaTitle,
            playerState: message.media.playerState,
        };
        const recreatedMedia = new NetflixViewing(
            partialWatchEntry.urlId,
            partialWatchEntry.showName,
            partialWatchEntry.playerState
        );
        viewingTracker.setCurrent(recreatedMedia);
        console.log(
            "Background received media state:",
            viewingTracker.currentMedia
        );
    } else if (message.event === "netflix_page_opened") {
        viewingTracker.reportNetflixWatchPage(message.media.pageId);
    }
    // Other existing message handling...
});
