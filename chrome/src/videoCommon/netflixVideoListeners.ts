// videoCommon/netflixVideoListeners.ts

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
 * Netflix uses a different player structure than YouTube.
 * This function attempts to find the video element in Netflix's player.
 */
function findNetflixVideoElement(): HTMLVideoElement | null {
    console.log("[Netflix] Searching for video element");

    // Try different selector strategies for Netflix
    const videoSelectors = [
        "video", // Standard video tag
        ".VideoContainer video", // Common Netflix container
        ".watch-video--player-view video", // Another possible Netflix structure
        "#appMountPoint video", // Netflix root mount point
        ".nf-player-container video", // Netflix player container
    ];

    let videoElement: HTMLVideoElement | null = null;

    for (const selector of videoSelectors) {
        const element = document.querySelector(selector) as HTMLVideoElement;
        if (element) {
            console.log(
                `[Netflix] Found video element using selector: ${selector}`
            );
            videoElement = element;
            break;
        }
    }

    return videoElement;
}

function attachNetflixVideoListeners(retries = 0, maxRetries = 15) {
    console.log("[Netflix] In attachNetflixVideoListeners, attempt:", retries);

    cleanupNetflixVideoListeners();

    const video = findNetflixVideoElement();
    console.log("[Netflix] Video element:", video);

    if (!video) {
        if (retries < maxRetries) {
            // Exponential backoff with a cap
            const dynamicMin = 1000 * Math.pow(1.5, retries);
            const delay = Math.min(dynamicMin, 10000);

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

    // Check if video is already playing (auto-started)
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

// Netflix sometimes loads its player dynamically or when
// transitioning between videos, so we use MutationObserver
// to detect changes
function setupMutationObserver() {
    console.log("[Netflix] Setting up MutationObserver");

    const observer = new MutationObserver((mutations) => {
        // Check if any mutations might have affected the video player
        const shouldCheckForVideo = mutations.some((mutation) => {
            // Check for added nodes that might contain a video
            if (mutation.addedNodes.length > 0) {
                return true;
            }

            // Check if attributes changed on elements that might contain a video
            if (
                mutation.type === "attributes" &&
                (mutation.target as Element).tagName === "DIV" &&
                (mutation.target as Element).classList.contains(
                    "player-timedtext"
                )
            ) {
                return true;
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
        attributeFilter: ["class", "style"],
    });

    return observer;
}

// Initialize when the script loads
function initialize() {
    console.log("[Netflix] Initializing video listeners");
    attachNetflixVideoListeners();

    const observer = setupMutationObserver();

    // Cleanup on page unload
    window.addEventListener("beforeunload", () => {
        console.log(
            "[Netflix] Page unloading, cleaning up listeners and observer"
        );
        cleanupNetflixVideoListeners();
        observer.disconnect();
    });

    window.addEventListener("unload", () => {
        cleanupNetflixVideoListeners();
        observer.disconnect();
    });
}

// Start the initialization process
initialize();
