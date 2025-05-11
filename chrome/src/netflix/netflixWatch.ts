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

import { historyTracker } from "./historyTrackerInit";

import { EL_IDS } from "./constants";

function getElementWithGivenIdOrThrow(id: string) {
    const element = document.getElementById(id);
    if (!element) {
        throw new MissingComponentError(`Misspelled or missing element: ${id}`);
    }
    return element;
}

function injectModal() {
    // Don't inject if modal already exists
    if (document.getElementById(EL_IDS.MODAL)) {
        return;
    }

    // Inject CSS
    const style = document.createElement("style");
    document.head.appendChild(style);

    // Inject HTML
    const div = document.createElement("div");
    div.innerHTML = modalHtml;
    // Append straight to the document body
    document.body.appendChild(div.firstElementChild!);

    // Wait for elements to be available
    const waitForElement = (
        selector: string,
        callback: (element: Element) => void
    ) => {
        console.log("In waiting for el");
        const element = document.getElementById(selector);
        if (element) {
            console.log("El exists");
            callback(element);
        } else {
            console.log("No el found, requesting animation frfame");
            setTimeout(() => {
                requestAnimationFrame(() => waitForElement(selector, callback));
            }, 2000);
        }
    };
    console.log("Waiting for element");
    waitForElement(EL_IDS.MODAL, (modal) => {
        // Now you can safely populate your dropdown
        console.log("Modal ready");
        const dropdown = getElementWithGivenIdOrThrow(EL_IDS.SERIES_SELECT);
        // Populate dropdown options here
        historyTracker.getTopFive().then((topFiveList) => {
            topFiveList.forEach((item) => {
                const option = document.createElement("option");
                option.value = item;
                option.textContent = item;
                dropdown.appendChild(option);
            });
        });
        console.log("Settin gup event listerners");
        // Add the rest of your event listeners
        setupEventListeners();
    });
}

function setupEventListeners() {
    console.log("Injecting listeners in setupEventListeners");
    // Add event listeners
    const modal = getElementWithGivenIdOrThrow(EL_IDS.MODAL);

    if (!modal) {
        throw new MissingComponentError("The whole modal");
    }

    document.body.appendChild(modal);

    const dropdownSection = getElementWithGivenIdOrThrow(
        EL_IDS.DROPDOWN_SECTION_DIV
    );
    const inputSection = getElementWithGivenIdOrThrow(EL_IDS.INPUT_SECTION_DIV);
    const newEntryBtn = getElementWithGivenIdOrThrow(EL_IDS.NEW_ENTRY_BTN);
    const cancelEntryBtn = getElementWithGivenIdOrThrow(
        EL_IDS.CANCEL_ENTRY_BTN
    );

    const confirmButton = getElementWithGivenIdOrThrow(EL_IDS.CONFIRM_BTN);
    const ignoreButton = getElementWithGivenIdOrThrow(EL_IDS.CANCEL_ENTRY_BTN);

    const seriesSelect = getElementWithGivenIdOrThrow(
        EL_IDS.SERIES_SELECT
    ) as HTMLSelectElement;

    const seriesInput = getElementWithGivenIdOrThrow(
        EL_IDS.SERIES_INPUT
    ) as HTMLInputElement;

    newEntryBtn.onclick = () => {
        dropdownSection.style.display = "none";
        inputSection.style.display = "block";
    };

    cancelEntryBtn.onclick = () => {
        inputSection.style.display = "none";
        dropdownSection.style.display = "block";
    };

    confirmButton.onclick = () => {
        console.log("In confirm btn onclick");
        const value =
            inputSection.style.display === "none"
                ? seriesSelect.value
                : seriesInput.value.trim();

        if (!value) return alert("Please enter or select a series name.");
        console.log("Saving ", value);
        // Save value to chrome.storage.local

        historyTracker.recordEnteredValue(value);

        modal.remove();
    };

    ignoreButton.onclick = () => {
        // Get current video URL or ID to ignore
        const currentUrl = window.location.href;
        console.log("current URL", currentUrl);

        // Save video to ignore list
        historyTracker.recordIgnoredUrl(currentUrl);

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
