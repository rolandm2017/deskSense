// background.ts
import { api } from "./api";
import { MissingUrlError } from "./errors";
import { getDomainFromUrl } from "./urlTools";
import { extractChannelInfoFromWatchPage } from "./youtube/channelExtractor";
import {
    extractChannelNameFromUrl,
    getYouTubeVideoId,
    isOnSomeChannel,
    isWatchingVideo,
    watchingShorts,
} from "./youtube/youtube";

import { viewingTracker, YouTubeViewing } from "./visits";

import { ignoredDomains, isDomainIgnored, loadDomains } from "./ignoreList";

/*

YouTube code, a lot of it lives here, because YouTube is monitored
from the background.ts script itself. 
This approach cannot work for Netflix. Much user input is needed there.

*/

// Code that lets you open the options page when the icon is clicked
// Disabled in favor of the modal
function openOptionsOnClickIcon() {
    chrome.action.onClicked.addListener(() => {
        chrome.runtime.openOptionsPage();
    });
}

// openOptionsOnClickIcon();

// // Handle YouTube URL specifically
function handleYouTubeUrl(
    tab: chrome.tabs.Tab,
    tabsWithIntervalsRecorder: Function
) {
    if (!tab.url || !tab.id || !tab.title) {
        console.warn("Missing required tab properties");
        return;
    }

    if (isWatchingVideo(tab.url)) {
        // YouTube does lots and lots of client side rendering, so
        // a short delay ensures that the page has fully loaded
        // Use executeScript to access the DOM on YouTube watch pages
        const tabId = tab.id;
        tabsWithIntervalsRecorder(tabId);
        setTimeout(() => {
            chrome.scripting.executeScript(
                {
                    target: { tabId: tabId },
                    func: extractChannelInfoFromWatchPage,
                },
                (results) => {
                    const tabTitle = tab.title ? tab.title : "Unknown Title";

                    let videoId;
                    if (tab.url) {
                        videoId = getYouTubeVideoId(tab.url);
                    } else {
                        videoId = "Missing URL";
                        throw new MissingUrlError();
                    }

                    let channelName = "Unknown Channel";
                    if (results && results[0] && results[0].result) {
                        // TODO: Get the video player info
                        channelName = results[0].result;
                    }
                    console.log(
                        "Detected ",
                        channelName,
                        " In new page",
                        tabTitle
                    );
                    const youTubeVisit = new YouTubeViewing(
                        videoId,
                        tabTitle,
                        channelName
                    );
                    // FIXME: You don't need to send the page notification.
                    // FIXME: The parent func will send it for us
                    // FIXME: "api.reportTabSwitch(domain, tab.title ? tab.title : "No title found");"
                    // youTubeVisit.sendInitialInfoToServer();
                    viewingTracker.setCurrent(youTubeVisit);
                }
            );
            // NOTE: ** do not change this 1500 ms delay **
            // was 1500 but tha'ts too short
        }, 2900); // 1.5 second delay. The absolute minimum value.
        // 1.0 sec delay still had the "prior channel reported as current" problem
    } else if (isOnSomeChannel(tab.url)) {
        // For channel pages, we can extract from the URL
        const channelName = extractChannelNameFromUrl(tab.url);
        api.reportYouTube(tab.title, channelName);
    } else if (watchingShorts(tab.url)) {
        // Avoids trying to extract the channel name from
        // the YouTube Shorts page. The page's HTML changes often. Sisyphean task.
        api.reportYouTube(tab.title, "Watching Shorts");
    } else {
        api.reportYouTube(tab.title, "YouTube Home");
    }
}

const tabsWithPollingList: number[] = [];

function putTabIdIntoList(tabId: number) {
    tabsWithPollingList.push(tabId);
}

interface ProcessedUrlEntry {
    timestamp: number;
    url: string;
}

// FIXME: What to do when the user visits the same URL 2-3x on multiple tabs?
const processedTabs = new Map<number, ProcessedUrlEntry>();

const PAGE_LOAD_DEBOUNCE_DELAY = 4000;

function getDomainFromUrlAndSubmit(tab: chrome.tabs.Tab) {
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
    const tabId = tab.id!;

    // Check if this tab with this URL was processed recently
    const lastProcessed = processedTabs.get(tabId);
    if (
        lastProcessed &&
        lastProcessed.url === tab.url &&
        now - lastProcessed.timestamp < PAGE_LOAD_DEBOUNCE_DELAY
    ) {
        console.log(
            "Skipping recently processed URL:",
            tab.url,
            "in tab:",
            tabId
        );
        return;
    }

    // Mark this URL as processed for this tab
    processedTabs.set(tabId, {
        timestamp: now,
        url: tab.url,
    });

    // Clean up old entries periodically
    // 12 chosen because it seems to only happen on youtube and refreshed pages
    if (processedTabs.size > 12) {
        const tabsToDelete: number[] = [];
        for (const [tabKey, entry] of processedTabs.entries()) {
            if (now - entry.timestamp > 10000) {
                // Remove entries older than 10 seconds
                tabsToDelete.push(tabKey);
            }
        }
        tabsToDelete.forEach((key) => processedTabs.delete(key));
    }

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
            handleYouTubeUrl(tab, putTabIdIntoList);
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

    // removeInfo contains additional information
    console.log("Window was closed:", removeInfo.isWindowClosing);

    const isYouTubeWatchPage = tabsWithPollingList.includes(tabId);

    // Perform any cleanup or final operations here
    if (isYouTubeWatchPage && viewingTracker.current) {
        // send final data to server
        // TODO: This actually ends THE VISIT because a visit is the time on a page!
        // The Viewing would be when the user hits Pause.
        viewingTracker.endViewing();
    }
});

function cancelPauseRecording(timeoutId: number) {
    clearTimeout(timeoutId);
}

let tempTimerVar = new Date();

let playCount = 0;
let pauseCount = 0;

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log(message, sender);
    let endSessionTimeoutId;
    if (message.event === "play") {
        playCount++;
        console.log("[onMsg] Play detected", playCount);
        if (endSessionTimeoutId) {
            console.log("[onMsg] Cancel pause viewing");
            const endOfIntervalTime = new Date();
            console.log(
                "[onMsg] DURATION: ",
                endOfIntervalTime.getSeconds() - tempTimerVar.getSeconds()
            );
            cancelPauseRecording(endSessionTimeoutId);
        }
        if (viewingTracker.current) {
            console.log("[onMsg] Starting time tracking");
            viewingTracker.current.startTimeTracking();
            return;
        } else {
            // it wasn't there yet because, the, the channel extractor
            // script didn't run yet but the "report playing video" code did
            if (sender.tab) {
                const tab = sender.tab;
                const tabUrl = tab.url;
                const tabTitle = tab.title || "Unknown Title";

                // Extract video ID from URL
                let videoId;
                if (tabUrl) {
                    // Handle any additional parameters after the video ID
                    videoId = getYouTubeVideoId(tabUrl);
                } else {
                    videoId = "Missing URL";
                    console.error("URL doesn't contain video ID parameter");
                }

                // TODO: Get channel name from somewhere
                const youTubeVisit = new YouTubeViewing(
                    videoId,
                    tabTitle,
                    "Unknown Channel"
                );
                youTubeVisit.sendInitialInfoToServer();
                viewingTracker.setCurrent(youTubeVisit);
            }
        }
    } else if (message.event === "pause") {
        pauseCount++;
        console.log("[onMsg] Pause detected", pauseCount);
        if (viewingTracker.current) {
            // TODO: Set delay to pause tracking
            console.log("[onMsg]START pause timer");
            tempTimerVar = new Date();

            const localTime = new Date();

            endSessionTimeoutId = setTimeout(() => {
                const endOfIntervalTime = new Date();
                console.log("[onMsg] Timer expired: pausing tracking");
                console.log("[onMsg] THIS PRITNS");
                console.log(
                    "[onMsg] DURATION 2: ",
                    endOfIntervalTime.getSeconds() - localTime.getSeconds()
                );
                if (viewingTracker.current) {
                    viewingTracker.current.pauseTracking();
                }
            }, 3000);
        }
    } else {
        console.log("Unknown event:", message);
    }
});

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
    // Make sure the service worker is ready before setting up listeners
    if (chrome.storage) {
        // Now it is safe to use chrome.storage
        // Listen for storage changes
        chrome.storage.onChanged.addListener((changes, area) => {
            if (area === "local" && changes.ignoredDomains) {
                console.log(
                    "Changes in ignoredDomains:",
                    changes.ignoredDomains
                );
                if (changes.ignoredDomains.newValue) {
                    ignoredDomains.addNew(changes.ignoredDomains.newValue);
                }
            } else {
                console.log("Other changes:", changes); // log other changes if needed
            }
        });
    } else {
        console.error("chrome.storage is not available!");
    }

    loadDomains();
});

/*
 * Open the Netflix Watch modal when you click the icon
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
