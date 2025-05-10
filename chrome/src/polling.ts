import { visitTracker } from "./visits";

import { TrackerInitializationError } from "./errors";

function executeTimeTrackingScript(tabId: number) {
    // used to run in handleYoutubeUrl
    chrome.scripting.executeScript(
        {
            target: { tabId: tabId },
            func: startVideoTimeTracking,
        }
        // adfadsfadsfasdfasf
        // take the player state, package it with prev func results, pass it to server
    );
}

// old listener for polling behavior
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "VIDEO_TIME") {
        console.log("Video timestamp:", message.time);
        // store, sync, or process time here
        if (visitTracker.current) {
            visitTracker.current.addTimestamp(message.time);
            const ready = visitTracker.timerElapsed();
            if (ready) {
                visitTracker.endVisit();
            }
        } else {
            throw new TrackerInitializationError();
        }
    }
});

// Polling Interval: "How often do we check if it's still playing?"
export const pollingInterval = 3000;
// Note that the interval must stay < 20 sec or so.
// Consider what happens if the interval is 180 sec, and
// the user pauses right after the 180 sec interval refreshes.
// The extension then believes the user is active for three minutes
// before it records that they have paused. A 20 sec interval might be okay.
// Could be YAGNI and KISS though.

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
            // Query "VIDEO_TIME" to find where this comes out
            chrome.runtime.sendMessage({ type: "VIDEO_TIME", time });
        }
    }, pollingInterval); // every 3 seconds
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
