import { reportTabSwitch } from "./api.js"

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
            console.log("New tab created:", domain)
            reportTabSwitch(domain)
        }
    }
})

// Listen for any tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete" && tab.url) {
        const domain = getDomainFromUrl(tab.url)
        if (domain) {
            console.log("Tab updated:", domain)
            reportTabSwitch(domain)
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
                reportTabSwitch(domain)
            }
        }
    })
})
