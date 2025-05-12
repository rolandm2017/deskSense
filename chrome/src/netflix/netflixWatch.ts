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

import reviewTitleComponent from "./reviewTitleComponent.html";
import selectTitleComponent from "./selectTitleComponent.html";

import { MissingComponentError } from "./errors";

import { historyTracker } from "./historyTrackerInit";

import { EL_IDS } from "./constants";

/* NOTES on what could be: 

* If you use the dropdown and feel like 5 entries isn't enough, 
* you could increase it to 8.
* 
* The "Don't ask again" btn could be "Mark Leisure" or "Mark Productivity"
* as a replacement for "Ignore". The server needs to categorize as one of the two.
* 
* KeepAlive can start right away.
* 
* Netflix and YouTube will share a lot of code.

*/

type ModalState = "selecting" | "review";

let currentModalState: ModalState = "selecting";
let selectedTitleState: string | null = null;

class ModalBase {
    wholeModal: HTMLElement;
    constructor() {
        this.wholeModal = getElementWithGivenIdOrThrow(EL_IDS.MODAL);
    }

    removeModal() {
        this.wholeModal.remove();
    }
}

class SelectingTitleModal {
    //
    constructor() {
        //
    }

    attachSelectingTitleListeners() {
        //
    }

    renderContainerContent() {
        //
    }

    cleanupEventListeners() {
        //
    }
}

class ReviewSelectionModal {
    //
    constructor() {
        //
    }

    switchToSelectingTitleState() {
        // set the modal state
        // switch the content
    }

    attachReviewSelectionListeners() {
        //
    }

    cleanupEventListeners() {
        //
    }
}

function getElementWithGivenIdOrThrow(id: string) {
    const element = document.getElementById(id);
    if (!element) {
        throw new MissingComponentError(`Misspelled or missing element: ${id}`);
    }
    return element;
}

function setCurrentReviewTitleIntoReviewComponent() {
    // need to inject the name at the right place
    const el = getElementWithGivenIdOrThrow(EL_IDS.CURRENT_TITLE_TARGET);
    if (!selectedTitleState) {
        throw new Error("Failed to set title upon selection");
    }
    el.innerText = selectedTitleState;
}

function renderModal(stateTargetContainer: HTMLElement) {
    if (currentModalState === "selecting") {
        stateTargetContainer.innerHTML = selectTitleComponent;
        attachSelectingTitleListeners();
    } else {
        stateTargetContainer.innerHTML = reviewTitleComponent;
        setCurrentReviewTitleIntoReviewComponent();
        attachConfirmedTitleListeners();
    }
}

function injectInitialStateModal() {
    // Don't inject if modal already exists
    if (document.getElementById(EL_IDS.MODAL)) {
        return;
    }

    // TODO: If (userSetEntry) displayEntry()

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
        const element = document.getElementById(selector);
        if (element) {
            console.log("El exists");
            callback(element);
        } else {
            console.log("No el found, requesting animation frfame");
            setTimeout(() => {
                requestAnimationFrame(() => waitForElement(selector, callback));
            }, 500);
        }
    };
    // console.log("Waiting for element", new Date().getSeconds());
    waitForElement(EL_IDS.MODAL, (modal) => {
        // Now you can safely populate your dropdown
        console.log("Modal ready", new Date().getSeconds());
        const dropdown = getElementWithGivenIdOrThrow(EL_IDS.SERIES_SELECT);
        // Populate dropdown options here
        historyTracker.getTopFive().then((topFiveList) => {
            topFiveList.forEach((item) => {
                // console.log("Top five list forEach", item);
                const option = document.createElement("option");
                option.value = item;
                option.textContent = item;
                dropdown.appendChild(option);
            });
        });
        // Add the rest of your event listeners
        attachSelectingTitleListeners();
    });
}

function closeModal(modal: HTMLElement) {
    modal.remove();
}

function attachConfirmedTitleListeners() {
    const modal = getElementWithGivenIdOrThrow(EL_IDS.MODAL);

    const changeTitleBtn = getElementWithGivenIdOrThrow(
        EL_IDS.CHANGE_TITLE_BTN
    );
    const closeModalBtn = getElementWithGivenIdOrThrow(EL_IDS.CLOSE_BTN);

    // Setup "Change title" listener
    changeTitleBtn.addEventListener("click", () => {
        //
        console.log("changing back to the prior state");
        // selectedTitleState = ""; // Don't change it yet. No point
        currentModalState = "selecting";
        const stateChangeTarget = getElementWithGivenIdOrThrow(
            EL_IDS.STATE_TARGET
        );
        renderModal(stateChangeTarget);
    });

    // Setup "Close" listener
    closeModalBtn.addEventListener("click", () => {
        //
        console.log("closing modal");
        closeModal(modal); //
    });
}

function attachSelectingTitleListeners() {
    console.log("Injecting listeners in setupEventListeners");
    // Add event listeners
    const modal = getElementWithGivenIdOrThrow(EL_IDS.MODAL);

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
        const mediaTitle =
            inputSection.style.display === "none"
                ? seriesSelect.value
                : seriesInput.value.trim();

        if (!mediaTitle) return alert("Please enter or select a series name.");
        console.log("Saving ", mediaTitle);
        selectedTitleState = mediaTitle;
        // Save mediaTitle to chrome.storage.local

        // TODO: If they select the wrong thing form the dropdown,
        // TODO: AND they hit Confirm,
        // then they can just open the modal again, select the right value,
        // click Confirm. And the program will end the incorrect session,
        // start them on the right one. They lose 2-3 min tracked in
        // the wrong spot.

        const currentUrl = window.location.href;

        // TEMP while testing on other pages:
        const tempUrl =
            "https://www.netflix.com/watch/81705696?trackId=272211954";
        historyTracker.recordEnteredMediaTitle(mediaTitle, tempUrl);

        // update for next time
        currentModalState = "review";

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

// TODO: Handle case where user closes the URL for a minute, comes back.
// the modal should be autofilled with the right selection. Just need "confirm"

let checkCount = 1;
// Wait for Netflix page to load and inject modal
const checkNetflixLoaded = () => {
    console.log("checkNetflixLoaded: " + checkCount, checkCount);
    console.log("check count: ", checkCount + checkCount, "foo");
    // You might want to add specific checks here for Netflix player
    if (document.readyState === "complete") {
        // Add a delay to ensure Netflix has fully loaded
        console.log("Injecting modal", new Date().getSeconds());
        injectInitialStateModal();
    } else {
        console.log("Checking document state again. Retry number:", checkCount);
        checkCount++;
        setTimeout(checkNetflixLoaded, 500);
    }
};

checkNetflixLoaded();

function openSelectingTitleModal() {
    injectInitialStateModal();
}

function openReviewTitleModal() {
    const style = document.createElement("style");
    document.head.appendChild(style);

    // Inject HTML
    const div = document.createElement("div");
    console.log("Putting modalHtml into reviewTitleModal");
    div.innerHTML = modalHtml;
    // Append straight to the document body
    document.body.appendChild(div.firstElementChild!);

    const stateTargetContainer = getElementWithGivenIdOrThrow(
        EL_IDS.STATE_TARGET
    );

    stateTargetContainer.innerHTML = reviewTitleComponent;
    setCurrentReviewTitleIntoReviewComponent();
    attachConfirmedTitleListeners();
}

function openModal() {
    if (currentModalState === "selecting") {
        openSelectingTitleModal();
    } else {
        openReviewTitleModal();
    }
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("** Received message:", message);
    console.log("** Page state: ", currentModalState);

    if (message.action === "openModal") {
        // Re-inject the modal
        // injectModal
        openModal();
        sendResponse({ success: true });
    }

    // Must return true to indicate you want to send a response asynchronously
    return true;
});
