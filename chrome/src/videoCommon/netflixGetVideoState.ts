// Netflix Video Player Status Checker

/*

Exists so the chrome.windows.onFocusChanged listener can ask Netflix's
Watch Page what the video player state is.

*/

/**
 * Netflix-specific function to find the video player element
 * Uses the same reliable selector strategy from your existing code
 */
function findNetflixVideoElement() {
    console.log("[Netflix Status] Searching for video element");

    // Try multiple selector strategies for Netflix's player
    const selectors = [
        "video", // Basic video tag
        ".watch-video--player-view video", // Netflix player view
        ".NFPlayer video", // Netflix player container
        "#appMountPoint video", // App mount point
        ".nf-player-container video", // Player container
        "#netflix-player video", // Netflix player ID
        "[data-uia='player'] video", // Player by data attribute
        ".VideoContainer video", // Video container
    ];

    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element && element instanceof HTMLVideoElement) {
            console.log(
                `[Netflix Status] Found video element using selector: ${selector}`
            );
            return element;
        }
    }

    // If selectors don't work, try finding any video element in the DOM
    const allVideos = document.getElementsByTagName("video");
    if (allVideos.length > 0) {
        console.log(
            `[Netflix Status] Found video element using getElementsByTagName`
        );
        return allVideos[0];
    }

    console.log("[Netflix Status] No video element found with any selector");
    return null;
}

/**
 * Simple function that just returns "paused" or "playing"
 */
export function getNetflixVideoStatus() {
    const video = findNetflixVideoElement();

    if (!video) {
        return "not_found";
    }

    return video.paused ? "paused" : "playing";
}
