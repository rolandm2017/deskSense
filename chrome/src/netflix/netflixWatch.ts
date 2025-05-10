// netflix/netflixWatch.ts

import modalHtml from "./netflixWatchModal.html";

function injectModal() {
    // Don't inject if modal already exists
    if (document.getElementById("watch-tracker-modal")) {
        return;
    }

    // Inject CSS
    const style = document.createElement("style");
    document.head.appendChild(style);

    // Inject HTML
    const div = document.createElement("div");
    div.innerHTML = modalHtml;
    document.body.appendChild(div.firstElementChild!);

    // Add event listeners
    const modal = document.getElementById("watch-tracker-modal");

    const dropdownSection = document.getElementById("dropdown-section");
    const inputSection = document.getElementById("input-section");
    const newEntryBtn = document.getElementById("new-entry-btn");
    const cancelEntryBtn = document.getElementById("cancel-entry-btn");

    newEntryBtn!.onclick = () => {
        dropdownSection!.style.display = "none";
        inputSection!.style.display = "block";
    };

    cancelEntryBtn!.onclick = () => {
        inputSection!.style.display = "none";
        dropdownSection!.style.display = "block";
    };

    document.getElementById("confirm-btn")!.onclick = () => {
        const value =
            inputSection!.style.display === "none"
                ? (
                      document.getElementById(
                          "series-select"
                      ) as HTMLSelectElement
                  ).value
                : (
                      document.getElementById(
                          "series-input"
                      ) as HTMLInputElement
                  ).value.trim();

        if (!value) return alert("Please enter or select a series name.");

        // Save value to chrome.storage.local
        chrome.storage.local.set({ currentWatching: value }, () => {
            console.log("Confirmed:", value);
        });

        document.getElementById("watch-tracker-modal")!.remove();
    };

    document.getElementById("ignore-btn")!.onclick = () => {
        // Get current video URL or ID to ignore
        const currentUrl = window.location.href;

        // Save video to ignore list
        chrome.storage.local.get(["ignoredVideos"], (result) => {
            const ignoredVideos = result.ignoredVideos || [];
            ignoredVideos.push(currentUrl);
            chrome.storage.local.set({ ignoredVideos }, () => {
                console.log("Ignored this video:", currentUrl);
            });
        });

        document.getElementById("watch-tracker-modal")!.remove();
    };
}

// Wait for Netflix page to load and inject modal
const checkNetflixLoaded = () => {
    // You might want to add specific checks here for Netflix player
    if (document.readyState === "complete") {
        // Add a delay to ensure Netflix has fully loaded
        setTimeout(injectModal, 2000);
    } else {
        setTimeout(checkNetflixLoaded, 500);
    }
};

checkNetflixLoaded();
