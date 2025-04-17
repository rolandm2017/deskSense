// background.js
import { reportTabSwitch, reportIgnoredUrl } from "./api.js"

chrome.action.onClicked.addListener(() => {
    chrome.runtime.openOptionsPage()
})

// Helper function to get domain from URL
export function getDomainFromUrl(urlString) {
    try {
        console.log(urlString)
        const url = new URL(urlString)
        return url.hostname
    } catch (e) {
        console.error("Invalid URL:", urlString)
        return null
    }
}

export function getDomainFromUrlAndSubmit(tab) {
    const domain = getDomainFromUrl(tab.url)
    if (domain) {
        console.log(domain, "22ru")
        const ignored = isDomainIgnored(domain, ignoredDomains)
        console.log(ignored, ignored === undefined, "24ru")
        if (ignored) {
            reportIgnoredUrl()
            return
        }
        console.log("New tab created:", domain, "Title:", tab.title)
        reportTabSwitch(domain, tab.title)
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

// /* * * *
//  *
//  * Ignored domains section
//  *
//  * * * *
//  */

// Load domains when extension starts
let ignoredDomains = []

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
                ignoredDomains = changes.ignoredDomains.newValue || []
            } else {
                console.log("Other changes:", changes) // log other changes if needed
            }
        })
    } else {
        console.error("chrome.storage is not available!")
    }

    loadDomains()
})

function loadDomains() {
    chrome.storage.local.get("ignoredDomains", (data) => {
        ignoredDomains = data.ignoredDomains || []
    })
}

// Example: Check if a domain is in the ignored list
export function isDomainIgnored(domain, ignoreList) {
    console.log(domain, "102ru")
    // const domain = new URL(url).hostname
    // console.log(domain, "104ru")
    console.log(ignoreList, "105ru")
    // TODO: Make it use binary search
    return ignoreList.some(
        (ignoredDomain) =>
            domain === ignoredDomain ||
            ignoredDomain.includes(domain) ||
            domain.includes(ignoredDomain)
    )
}

// // Now you can implement your domain blocking/ignoring logic here
// // using the isDomainIgnored function
