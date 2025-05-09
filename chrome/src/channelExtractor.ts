// channelExtractor.ts

declare global {
    interface Window {
        videoTimeTrackerId?: number;
        __videoTimeIntervalStarted?: boolean;
    }
}

function markIntervalStarted(window: Window) {
    // This flag prevents multiple intervals from being set in the same tab.
    // YouTube pages can trigger repeated script injections (e.g. via navigation),
    // and without this check, we'd end up logging or sending duplicate timestamps.
    // Setting a flag on `window` ensures it's scoped to the tab's page context.
    // This way, only one tracker runs per video page.
    window.__videoTimeIntervalStarted = true;
}

export function startVideoTimeTracking() {
    const additionalIntervalWouldBeDuplicate =
        window.__videoTimeIntervalStarted;
    if (additionalIntervalWouldBeDuplicate) return;
    markIntervalStarted(window);

    // TODO: Make a way to stop this interval. so it doesn't run forever
    const intervalId: number = window.setInterval(() => {
        const video = document.querySelector("video");
        const time = video?.currentTime;
        if (typeof time === "number") {
            chrome.runtime.sendMessage({ type: "VIDEO_TIME", time });
        }
    }, 3000); // every 3 seconds
    window.videoTimeTrackerId = intervalId;
    // to cancel:
    // clearInterval(intervalId);
}

export function stopVideoTimeTracking() {
    if (window.videoTimeTrackerId) {
        clearInterval(window.videoTimeTrackerId);
        window.videoTimeTrackerId = undefined;
        return true;
    }
    return false;
}

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
    const channelElement = document.querySelector("ytd-channel-name a");

    let channelName =
        channelElement && channelElement.textContent
            ? channelElement.textContent.trim()
            : null;

    // Fallback to alternative selectors if the primary one fails
    if (!channelName) {
        const altChannelElement = document.querySelector("#owner-name a");
        channelName =
            altChannelElement && altChannelElement.textContent
                ? altChannelElement.textContent.trim()
                : "Unknown Channel";
    }

    return channelName;
}

// Function to extract channel name from YouTube Shorts
export function extractChannelInfoFromShortsPage() {
    /*
     * Here be dragons
     */
    return false;
}
