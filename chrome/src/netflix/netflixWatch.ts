// netflix/netflixWatch.ts

/*
 *
 * This file adds the modal.
 *
 * The file makes it accept user input and show data from storage.
 *
 * A layer between the UI and the rest of the system.
 *
 */

import modalHtml from "./netflixWatchModal.html";

import { MissingComponentError } from "./errors";

import { historyTracker } from "./historyTracker";

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

    // Wait for elements to be available
    const waitForElement = (
        selector: string,
        callback: (element: Element) => void
    ) => {
        const element = document.querySelector(selector);
        if (element) {
            callback(element);
        } else {
            requestAnimationFrame(() => waitForElement(selector, callback));
        }
    };

    waitForElement("#watch-tracker-modal", (modal) => {
        // Now you can safely populate your dropdown
        const dropdown = document.getElementById("series-select");
        if (dropdown) {
            // Populate dropdown options here
            historyTracker.getTopFive().then((topFiveList) => {
                topFiveList.forEach((item) => {
                    const option = document.createElement("option");
                    option.value = item;
                    option.textContent = item;
                    dropdown.appendChild(option);
                });
            });
        } else {
            throw new MissingComponentError("Missing series select");
        }

        // Add the rest of your event listeners
        setupEventListeners();
    });
}

function setupEventListeners() {
    // Add event listeners
    const modal = document.getElementById("watch-tracker-modal");

    if (!modal) {
        throw new MissingComponentError("The whole modal");
    }

    document.body.appendChild(modal);

    const dropdownSection = document.getElementById("dropdown-section");
    const inputSection = document.getElementById("input-section");
    const newEntryBtn = document.getElementById("new-entry-btn");
    const cancelEntryBtn = document.getElementById("cancel-entry-btn");

    if (!newEntryBtn || !dropdownSection || !inputSection || !cancelEntryBtn) {
        throw new MissingComponentError("Buttons or dropdown");
    }

    newEntryBtn.onclick = () => {
        dropdownSection.style.display = "none";
        inputSection.style.display = "block";
    };

    cancelEntryBtn.onclick = () => {
        inputSection.style.display = "none";
        dropdownSection.style.display = "block";
    };

    const confirmButton = document.getElementById("confirm-btn");

    if (!confirmButton) {
        throw new MissingComponentError("Confirm button");
    }

    confirmButton.onclick = () => {
        const value =
            inputSection.style.display === "none"
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

        historyTracker.recordEnteredValue(value);

        modal.remove();
    };

    const ignoreButton = document.getElementById("ignore-btn");

    if (!ignoreButton) {
        throw new MissingComponentError("Ignore button");
    }

    ignoreButton.onclick = () => {
        // Get current video URL or ID to ignore
        const currentUrl = window.location.href;
        console.log("current URL", currentUrl);

        // Save video to ignore list
        historyTracker.handleIgnoreUrl(currentUrl);

        modal.remove();
    };
}

let checkCount = 1;
// Wait for Netflix page to load and inject modal
const checkNetflixLoaded = () => {
    // You might want to add specific checks here for Netflix player
    if (document.readyState === "complete") {
        // Add a delay to ensure Netflix has fully loaded
        console.log("Injecting modal");
        setTimeout(injectModal, 2000);
    } else {
        console.log("Checking again for check number", checkCount);
        checkCount++;
        setTimeout(checkNetflixLoaded, 500);
    }
};

checkNetflixLoaded();
