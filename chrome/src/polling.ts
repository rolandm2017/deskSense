import { viewingTracker } from "./videoCommon/visits";

import { TrackerInitializationError } from "./errors";

/*

* Some old code that could be used for a polling approach to tracking watch time.

*/

class ViewingPayloadTimer {
    // a timer that tracks when to dispatch payload. KISS. Minimal.
    dispatchTime: Date;

    // TODO: Every two minutes send a KeepAlive signal: "Yep, still here"
    // If no KeepAlive signal, end session after five minutes.

    /*

    YouTube is a mixture of play/pause plus polling.

    */

    constructor(dispatchTime: Date) {
        this.dispatchTime = dispatchTime;
    }

    timerHasElapsed(currentTime: Date) {
        const hoursElapsed =
            currentTime.getHours() >= this.dispatchTime.getHours();
        if (hoursElapsed) {
            // if the hours has elapsed, the rest is irrelevant
            return true;
        }
        const minutesElapsed =
            currentTime.getMinutes() >= this.dispatchTime.getMinutes();
        if (minutesElapsed) {
            // if the minutes has elapsed, the seconds are irrelevant
            return true;
        }
        const secondsElapsed =
            currentTime.getSeconds() >= this.dispatchTime.getSeconds();
        if (secondsElapsed) {
            return true;
        }
        return false;
    }
}

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
        if (viewingTracker.currentMedia) {
            // viewingTracker.currentMedia.addTimestamp(message.time);
            // const ready = viewingTracker.timerElapsed();
            const ready = "temp";
            if (ready) {
                viewingTracker.endViewing();
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
    // Keep this in this window
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
