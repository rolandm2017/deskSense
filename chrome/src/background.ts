// background.js
import { reportTabSwitch, reportIgnoredUrl, reportYouTube } from "./api"
import { getDomainFromUrl } from "./urlTools"
import {
    extractChannelInfoFromWatchPage,
    extractChannelInfoFromShortsPage,
} from "./channelExtractor"
import {
    isWatchingVideo,
    isOnSomeChannel,
    extractChannelNameFromUrl,
    watchingShorts,
} from "./youtube"

import { isDomainIgnored, loadDomains, ignoredDomains } from "./ignoreList"

function openOptionsOnClickIcon() {
    chrome.action.onClicked.addListener(() => {
        chrome.runtime.openOptionsPage()
    })
}

openOptionsOnClickIcon()

// // Handle YouTube URL specifically
function handleYouTubeUrl(tab: chrome.tabs.Tab) {
    if (!tab.url || !tab.id || !tab.title) {
        console.warn("Missing required tab properties")
        return
    }

    if (isWatchingVideo(tab.url)) {
        // YouTube does lots and lots of client side rendering, so
        // a short delay ensures that the page has fully loaded
        // Use executeScript to access the DOM on YouTube watch pages
        const tabId = tab.id
        setTimeout(() => {
            chrome.scripting.executeScript(
                {
                    target: { tabId: tabId },
                    func: extractChannelInfoFromWatchPage,
                },
                (results) => {
                    if (results && results[0] && results[0].result) {
                        reportYouTube(tab.title, results[0].result)
                    } else {
                        reportYouTube(tab.title, "Unknown Channel")
                    }
                }
            )
        }, 1500) // 1.5 second delay - adjust as needed
        // 1.0 sec delay still had the "prior channel reported as current" problem
    } else if (isOnSomeChannel(tab.url)) {
        // For channel pages, we can extract from the URL
        const channelName = extractChannelNameFromUrl(tab.url)
        reportYouTube(tab.title, channelName)
    } else if (watchingShorts(tab.url)) {
        // Avoids trying to extract the channel name from
        // the YouTube Shorts page. The page's HTML changes often.
        reportYouTube(tab.title, "Watching Shorts")
    } else {
        reportYouTube(tab.title, "YouTube Home")
    }
}

function getDomainFromUrlAndSubmit(tab: chrome.tabs.Tab) {
    console.log("Tab.url", tab.url)
    if (tab.url === undefined) {
        console.error("No url found")
        return
    }
    const domain = getDomainFromUrl(tab.url)
    if (domain) {
        const ignored = isDomainIgnored(domain, ignoredDomains.getAll())
        // console.log(ignored, ignored === undefined, "224ru")
        if (ignored) {
            reportIgnoredUrl()
            return
        }
        const isYouTube = domain.includes("youtube.com")
        if (isYouTube) {
            console.log("[info] on YouTube")
            // Use the dedicated function to handle YouTube URLs
            handleYouTubeUrl(tab)
            return
        }
        console.log("New tab created:", domain, "\tTitle:", tab.title)
        reportTabSwitch(domain, tab.title ? tab.title : "No title found")
    } else {
        console.log("No domain found for ", tab.url)
    }
}

// New tab created
chrome.tabs.onCreated.addListener((tab) => {
    if (tab.url) {
        getDomainFromUrlAndSubmit(tab)
    }
})

// Listen for any tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete" && tab.url) {
        getDomainFromUrlAndSubmit(tab)
    }
})

// Listen for tab switches
chrome.tabs.onActivated.addListener((activeInfo) => {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        if (tab.url) {
            getDomainFromUrlAndSubmit(tab)
        }
    })
})

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
                )
                if (changes.ignoredDomains.newValue) {
                    ignoredDomains.addNew(changes.ignoredDomains.newValue)
                }
            } else {
                console.log("Other changes:", changes) // log other changes if needed
            }
        })
    } else {
        console.error("chrome.storage is not available!")
    }

    loadDomains()
})
