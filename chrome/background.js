// background.js
import { reportTabSwitch } from "./api.js"

chrome.action.onClicked.addListener(() => {
    chrome.runtime.openOptionsPage()
})

// Helper function to get domain from URL
function getDomainFromUrl(urlString) {
    try {
        const url = new URL(urlString)
        return url.hostname
    } catch (e) {
        console.error("Invalid URL:", urlString)
        return null
    }
}

// New tab created
chrome.tabs.onCreated.addListener((tab) => {
    if (tab.url) {
        const domain = getDomainFromUrl(tab.url)
        if (domain) {
            const ignored = isDomainIgnored(domain)
            if (ignored) {
                reportTabSwitch("Ignored", "Ignored")
                return
            }
            console.log("New tab created:", domain, "Title:", tab.title)
            reportTabSwitch(domain, tab.title)
        }
    }
})

// Listen for any tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete" && tab.url) {
        const domain = getDomainFromUrl(tab.url)
        if (domain) {
            console.log(tab, "31ru")
            console.log("Tab updated:", domain, "Title:", tab.title)
            reportTabSwitch(domain, tab.title)
        }
    }
})

// Listen for tab switches
chrome.tabs.onActivated.addListener((activeInfo) => {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        if (tab.url) {
            const domain = getDomainFromUrl(tab.url)
            if (domain) {
                console.log("Switched to tab:", domain)
                console.log("Title:", tab)
                reportTabSwitch(domain, tab.title)
            }
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
function isDomainIgnored(url) {
    const domain = new URL(url).hostname
    return ignoredDomains.some(
        (ignoredDomain) =>
            domain === ignoredDomain || domain.endsWith("." + ignoredDomain)
    )
}

// // Now you can implement your domain blocking/ignoring logic here
// // using the isDomainIgnored function
