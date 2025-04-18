import { ImpossibleToGetHereError, ChannelPageOnlyError } from "./errors"
import { stripProtocol } from "./urlTools"

/*
 * For YouTube, some channels are productive; others are not.
 *
 * User must be able to tag which channel is which.
 *
 * The extension must be able to tell which channel is active.
 */

// youtube.js
let lastReportedUrl = ""
let lastReportedChannel = ""
let activeTabInterval

export function getYouTubeChannel(youTubeUrl) {
    // try this way first
    if (isWatchingVideo(youTubeUrl)) {
        return extractChannelInfoFromWatchPage()
    } else if (isOnSomeChannel(youTubeUrl)) {
        return extractChannelNameFromUrl(youTubeUrl)
    } else {
        console.log("Cannot get channel name from ", youTubeUrl)
        return null
    }
}

// Extract channel name from YouTube page
export function extractChannelInfoFromWatchPage() {
    // Modern YouTube channel selector
    const channelElement = document.querySelector("ytd-channel-name a")
    let channelName = channelElement ? channelElement.textContent.trim() : null

    // Fallback to alternative selectors if the primary one fails
    if (!channelName) {
        const altChannelElement = document.querySelector("#owner-name a")
        channelName = altChannelElement
            ? altChannelElement.textContent.trim()
            : "Unknown Channel"
    }

    return channelName
}

export function isWatchingVideo(youTubeUrl) {
    return youTubeUrl.includes("youtube.com/watch")
}

export function isOnSomeChannel(youTubeUrl) {
    return youTubeUrl.includes("@")
}
// TODO: Extract channel from shorts
export function detectTypeOfYouTubePage(youTubeUrl) {
    const onBaseUrl = youTubeUrl.endsWith("youtube.com")
    const isOnSomeChannel = youTubeUrl.includes("@")
    const isWatchingVideo = youTubeUrl.includes("youtube.com/watch")
    if (onBaseUrl) {
        // is on JUST youtube
        return false
    } else if (isOnSomeChannel) {
        return true
    } else if (isWatchingVideo(youTubeUrl)) {
        return false
    } else {
        throw ImpossibleToGetHereError("Expected either")
    }
}

export function extractChannelNameFromUrl(youTubeUrl) {
    const onSomeChannelsPage = youTubeUrl.includes("@")
    if (onSomeChannelsPage) {
        // https://www.youtube.com/@pieceoffrench
        // https://www.youtube.com/@pieceoffrench/featured
        // https://www.youtube.com/@pieceoffrench/videos
        // https://www.youtube.com/@pieceoffrench/streams
        const segments = stripProtocol(youTubeUrl).split("/")
        return segments[1].slice(1)
    }
    throw ChannelPageOnlyError("Was not on a channel page")
}

// Initial check when the page loads
function checkForYouTubeVideo() {
    const currentUrl = window.location.href

    if (currentUrl.includes("youtube.com/watch")) {
        // Wait a bit for YouTube's dynamic content to load
        setTimeout(() => {
            const channelName = extractChannelInfo()
            reportChannelVisit(channelName, currentUrl)
        }, 1500)
    }
}

// // background.js
// chrome.runtime.onInstalled.addListener(() => {
//     // Set up alarms for periodic background syncing if needed
//     chrome.alarms.create("syncWatchData", { periodInMinutes: 15 })
// })

// chrome.alarms.onAlarm.addListener((alarm) => {
//     if (alarm.name === "syncWatchData") {
//         // Optional: Perform background sync of any cached data
//     }
// })
