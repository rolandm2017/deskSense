// src/netflixVideoListeners.ts

export {}; // make ts ignore declaring global here

declare global {
    interface Window {
        __netflixVideoElement: HTMLVideoElement | null;
    }
}

// Store references to event handlers
let playHandler: EventListener | null = null;
let pauseHandler: EventListener | null = null;

/**
 * Netflix-specific function to find the video player element
 * Netflix's player can be in different DOM locations
 */
function findNetflixVideoElement(): HTMLVideoElement | null {
    console.log("[Netflix] Searching for video element");

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
        const element = document.querySelector(selector) as HTMLVideoElement;
        if (element && element instanceof HTMLVideoElement) {
            console.log(
                `[Netflix] Found video element using selector: ${selector}`
            );
            return element;
        }
    }

    // If selectors don't work, try finding any video element in the DOM
    const allVideos = document.getElementsByTagName("video");
    if (allVideos.length > 0) {
        console.log(`[Netflix] Found video element using getElementsByTagName`);
        return allVideos[0];
    }

    console.log("[Netflix] No video element found with any selector");
    return null;
}

function attachNetflixVideoListeners(retries = 0, maxRetries = 15) {
    console.log(
        `[Netflix] In attachNetflixVideoListeners, attempt: ${retries}`
    );

    // Clean up existing listeners
    cleanupNetflixVideoListeners();

    // Try to find the video element
    const video = findNetflixVideoElement();
    console.log("[Netflix] Video element:", video);

    if (!video) {
        if (retries < maxRetries) {
            // Netflix can take time to load its player, use exponential backoff
            const delay = Math.min(1000 * Math.pow(1.5, retries), 10000);
            console.log(
                `[Netflix] Video element not found. Retrying in ${delay}ms (${
                    retries + 1
                }/${maxRetries})`
            );

            setTimeout(
                () => attachNetflixVideoListeners(retries + 1, maxRetries),
                delay
            );
        } else {
            console.error(
                "[Netflix] Failed to find video element after",
                maxRetries,
                "attempts"
            );
        }
        return;
    }

    console.log("[Netflix] Injecting video listeners");

    // Define handler functions and store references
    playHandler = () => {
        console.log("[Netflix] Sending play message");
        chrome.runtime.sendMessage({
            event: "user_pressed_play",
            source: "netflix",
        });
    };

    pauseHandler = () => {
        console.log("[Netflix] Sending pause message");
        chrome.runtime.sendMessage({
            event: "user_pressed_pause",
            source: "netflix",
        });
    };

    // Attach listeners
    video.addEventListener("play", playHandler);
    video.addEventListener("pause", pauseHandler);

    // Check if video is already playing
    const videoAutostarted = !video.paused;
    if (videoAutostarted) {
        console.log(
            "[Netflix] One-off auto-start for recording on page load / refresh"
        );
        chrome.runtime.sendMessage({
            event: "user_pressed_play",
            source: "netflix",
        });
    }

    window.__netflixVideoElement = video;
}

function cleanupNetflixVideoListeners() {
    // If we have a stored video element and handlers
    if (window.__netflixVideoElement) {
        const video = window.__netflixVideoElement;

        if (playHandler) {
            video.removeEventListener("play", playHandler);
        }

        if (pauseHandler) {
            video.removeEventListener("pause", pauseHandler);
        }

        // Clear references
        window.__netflixVideoElement = null;
        playHandler = pauseHandler = null;

        console.log("[Netflix] Cleaned up video listeners");
    }
}

// Netflix can load its player dynamically, especially when browsing
function setupMutationObserver() {
    console.log("[Netflix] Setting up MutationObserver");

    const observer = new MutationObserver((mutations) => {
        // Check if we need to look for the video element again
        const shouldCheckForVideo = mutations.some((mutation) => {
            // Check for added nodes
            if (mutation.addedNodes.length > 0) {
                for (let i = 0; i < mutation.addedNodes.length; i++) {
                    const node = mutation.addedNodes[i];
                    if (node instanceof HTMLElement) {
                        // Look for elements that might contain the video player
                        if (
                            node.tagName === "VIDEO" ||
                            node.classList.contains("nf-player-container") ||
                            node.querySelector("video")
                        ) {
                            return true;
                        }
                    }
                }
            }

            return false;
        });

        if (shouldCheckForVideo && !window.__netflixVideoElement) {
            console.log(
                "[Netflix] DOM changes detected, checking for video element"
            );
            attachNetflixVideoListeners();
        }
    });

    // Observe the entire document for changes
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["class", "style", "src"],
    });

    return observer;
}

// Initialize everything
console.log("[Netflix] In attachNetflixVideoListeners, attempt: 0");
attachNetflixVideoListeners();

// Setup mutation observer to catch dynamic changes
const observer = setupMutationObserver();

// Add cleanup when navigating away
window.addEventListener("beforeunload", () => {
    console.log("[Netflix] Page unloading, cleaning up");
    cleanupNetflixVideoListeners();
    observer.disconnect();
});

window.addEventListener("unload", () => {
    cleanupNetflixVideoListeners();
    observer.disconnect();
});
