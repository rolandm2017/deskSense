// background.ts
import { api } from "./api";
import {
    extractChannelInfoFromWatchPage,
    startVideoTimeTracking,
} from "./channelExtractor";
import { getDomainFromUrl } from "./urlTools";
import {
    extractChannelNameFromUrl,
    isOnSomeChannel,
    isWatchingVideo,
    watchingShorts,
} from "./youtube";

import { ignoredDomains, isDomainIgnored, loadDomains } from "./ignoreList";

function openOptionsOnClickIcon() {
    chrome.action.onClicked.addListener(() => {
        chrome.runtime.openOptionsPage();
    });
}

openOptionsOnClickIcon();

// // Handle YouTube URL specifically
function handleYouTubeUrl(tab: chrome.tabs.Tab) {
    if (!tab.url || !tab.id || !tab.title) {
        console.warn("Missing required tab properties");
        return;
    }

    if (isWatchingVideo(tab.url)) {
        // YouTube does lots and lots of client side rendering, so
        // a short delay ensures that the page has fully loaded
        // Use executeScript to access the DOM on YouTube watch pages
        const tabId = tab.id;
        setTimeout(() => {
            chrome.scripting.executeScript(
                {
                    target: { tabId: tabId },
                    func: extractChannelInfoFromWatchPage,
                },
                (results) => {
                    if (results && results[0] && results[0].result) {
                        // TODO: Get the video player info
                        api.reportYouTube(tab.title, results[0].result);
                    } else {
                        api.reportYouTube(tab.title, "Unknown Channel");
                    }
                    // Now start tracking video time
                    chrome.scripting.executeScript(
                        {
                            target: { tabId: tabId },
                            func: startVideoTimeTracking,
                        },
                        (results) => {
                            // adfadsfadsfasdfasf
                            // take the player state, package it with prev func results, pass it to server
                        }
                    );
                }
            );
            // NOTE: ** do not change this 1500 ms delay **
        }, 1500); // 1.5 second delay. The absolute minimum value.
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

function getDomainFromUrlAndSubmit(tab: chrome.tabs.Tab) {
    console.log("Tab.url", tab.url);
    if (tab.url === undefined) {
        console.error("No url found");
        return;
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
            handleYouTubeUrl(tab);
            return;
        }
        console.log("New tab created:", domain, "\tTitle:", tab.title);
        api.reportTabSwitch(domain, tab.title ? tab.title : "No title found");
    } else {
        console.log("No domain found for ", tab.url);
    }
}

// New tab created
chrome.tabs.onCreated.addListener((tab) => {
    if (tab.url) {
        getDomainFromUrlAndSubmit(tab);
    }
});

/*
 * Claude says:
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
    if (changeInfo.status === "complete" && tab.url) {
        getDomainFromUrlAndSubmit(tab);
    }
});

// Listen for tab switches
chrome.tabs.onActivated.addListener((activeInfo) => {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        if (tab.url) {
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
