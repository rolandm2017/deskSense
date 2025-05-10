// netflixBrowse.ts

// https://www.netflix.com/browse?jbv=81939610
// https://www.netflix.com/browse?jbv=81417684
// shows the series title

function obtuseConsoleLog() {
    console.log("############");
    console.log("######6#####");
    console.log("#######5####");
    console.log("########4###");
    console.log("#########3##");
    console.log("##########2#");
    console.log("############");
}

obtuseConsoleLog();

let titleEventHandlers = new Map();

interface CleanupHandler {
    type: string;
    handler: EventListener;
    options?: boolean | AddEventListenerOptions | undefined;
}
let pageCleanupHandlers: CleanupHandler[] = [];

// Option 1: Event Delegation (Most Efficient)

function setupClosestStyleListener() {
    const closestElHandler = (e: Event) => {
        // Find the closest video title element
        if (e.target && e.target instanceof Element) {
            const titleElement = e.target.closest("h2, h3, h4, .title-class");

            if (titleElement) {
                console.log("Clicked on:", titleElement.textContent);
                // Your tracking logic here
            }
        } else {
            console.warn("Found no target");
        }
    };

    document.addEventListener("click", closestElHandler, true);

    // Store reference for cleanup
    pageCleanupHandlers.push({
        type: "mouseover",
        handler: closestElHandler,
        options: true,
    });
}

// Option 2: Hover-to-Register Pattern
function handleTitleClick(e: MouseEvent) {
    console.log("GOAL GOAL GOAL GOAL");
    console.log("GOAL GOAL GOAL GOAL");
    console.log("GOAL GOAL GOAL GOAL");
    console.log("GOAL GOAL GOAL GOAL");
    // Your tracking logic here
    console.log("target", e.target);
    if (e.target instanceof Element) {
        console.log("closest", e.target.closest);
    } else {
        console.log("Not an element");
    }
}
function setupTitleEventListeners() {
    const mouseoverHandler = (e: Event) => {
        if (e.target instanceof Element) {
            const titleElement = e.target.closest("div");
            if (
                titleElement &&
                titleElement instanceof HTMLElement &&
                !titleElement.dataset.listenerAdded
            ) {
                titleElement.addEventListener("click", handleTitleClick);
                titleElement.dataset.listenerAdded = "true";

                // Store reference for cleanup
                titleEventHandlers.set(titleElement, handleTitleClick);
            }
        }
    };

    document.addEventListener("mouseover", mouseoverHandler, true);

    // Store reference for cleanup
    pageCleanupHandlers.push({
        type: "mouseover",
        handler: mouseoverHandler,
        options: true,
    });
}

console.log("Hi from roly");
console.log("The script loaded");
console.log("The script loaded");
console.log("The script loaded");
console.log("The script loaded");
console.log("The script loaded");

// Option (3) "ready, fire, aim"
// This will log every single click on the page

function putListenerEverywhere() {
    const everywhereListener = (e: Event) => {
        console.log("Clicked element:", e.target);
        if (e.target) {
            if (e.target instanceof Element) {
                console.log("Element tag:", e.target.tagName);
                console.log("Element text:", e.target.textContent);
                console.log("Element id:", e.target.id);
                console.log("Element classes:", e.target.className);
                console.log("-------------------");
            } else {
                console.log("SURPRISE! not an element");
            }
        }
    };
    document.addEventListener("click", everywhereListener, true); // Use capture phase to make sure we catch everything

    // Store reference for cleanup
    pageCleanupHandlers.push({
        type: "mouseover",
        handler: everywhereListener,
        options: true,
    });
}

// Cleanup function
function cleanup() {
    console.log("Cleaning up content script...");

    // Remove all title click listeners
    titleEventHandlers.forEach((handler, element) => {
        element.removeEventListener("click", handler);
        delete element.dataset.listenerAdded;
    });
    titleEventHandlers.clear();

    // Remove page-level event listeners
    pageCleanupHandlers.forEach(({ type, handler, options }) => {
        document.removeEventListener(type, handler, options);
    });
    pageCleanupHandlers = [];
}
