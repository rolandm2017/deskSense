//  videoCommon/youTubeVideoListeners.ts

/*

*/

// Note that this:
//             "run_at": "document_start"
// Would run way too early. As per Claude:
// """
// document_start - Chrome injects the script as soon as possible
// after the document element is created, but
// before any other DOM is constructed or loaded.
// """
// "document_end" is "after the DOM is complete but before subresources (images, etc.) finish loading."

export {}; // make ts ignore declaring global here

declare global {
    // Don't move this from this file
    interface Window {
        __videoElement: HTMLVideoElement | null;
    }
}

// Store references to event handlers
let playHandler: EventListener | null = null;
let pauseHandler: EventListener | null = null;

function attachVideoListeners(retries = 0, maxRetries = 10) {
    console.log("In attachVideoListeners");
    const video = document.querySelector("video");
    console.log(video, "video");

    cleanupVideoListeners();

    if (!video) {
        if (retries < maxRetries) {
            const dynamicMin = 1000 * Math.pow(1.5, retries);
            setTimeout(
                () => attachVideoListeners(retries + 1, maxRetries),
                Math.min(dynamicMin, 10000)
            );
        } else {
            console.error(
                "Failed to find video element after",
                maxRetries,
                "attempts"
            );
        }
        return;
    }

    console.log("Injecting video listeners");
    // Define handler functions and store references
    playHandler = () => {
        console.log("Sending play message");
        // TODO: Distinguish between Netflix Play, YouTube Play
        chrome.runtime.sendMessage({ event: "user_pressed_play" });
    };

    pauseHandler = () => {
        console.log("Sending *pause message");
        chrome.runtime.sendMessage({ event: "user_pressed_pause" });
    };

    // Attach listeners
    video.addEventListener("play", playHandler);
    video.addEventListener("pause", pauseHandler);

    const videoAutostarted = !video.paused;
    if (videoAutostarted) {
        console.log("One-off auto-start for recording on page load / refresh");
        chrome.runtime.sendMessage({ event: "user_pressed_play" });
    }

    window.__videoElement = video;
}

attachVideoListeners();

function cleanupVideoListeners() {
    // If we have a stored video element and handlers
    if (window.__videoElement) {
        const video = window.__videoElement;

        if (playHandler) {
            video.removeEventListener("play", playHandler);
        }

        if (pauseHandler) {
            video.removeEventListener("pause", pauseHandler);
        }

        // Clear references
        window.__videoElement = null;
        playHandler = pauseHandler = null;

        console.log("Cleaned up video listeners");
    }
}

// Automatic cleanup when page unloads
window.addEventListener("beforeunload", () => {
    console.log("[Content Script] Page unloading, cleaning up listeners");
    cleanupVideoListeners();
});

// You can also add redundant cleanup for the unload event
window.addEventListener("unload", () => {
    cleanupVideoListeners();
});
