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

export function askYouTubePlayerState(retries = 0, maxRetries = 10) {
    console.log("In attachVideoListeners");
    const video = document.querySelector("video");
    console.log(video, "video");

    if (!video) {
        console.error("Failed to find video element");
        return "Player Not Found";
    }

    return video.paused ? "paused" : "playing";
}
