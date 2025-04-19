// channelExtractor.js

/*
 * It's necessary to run this using chrome.scripting.executeScript.
 *
 * The bad alternative was to run a content script, and orchestrate complex, finnicky
 * message passing from content script to background script.
 *
 * Note that the below code, "document.querySelector," will not work in
 * a background script, which, this is, and must stay as.
 *
 */

// This function will run in the context of the YouTube page
export function extractChannelInfoFromWatchPage() {
    // Modern YouTube channel selector
    const channelElement = document.querySelector("ytd-channel-name a")

    let channelName =
        channelElement && channelElement.textContent
            ? channelElement.textContent.trim()
            : null

    // Fallback to alternative selectors if the primary one fails
    if (!channelName) {
        const altChannelElement = document.querySelector("#owner-name a")
        channelName =
            altChannelElement && altChannelElement.textContent
                ? altChannelElement.textContent.trim()
                : "Unknown Channel"
    }

    return channelName
}

// Function to extract channel name from YouTube Shorts
export function extractChannelInfoFromShortsPage() {
    /*
     * Here be dragons
     */
    return false
}
