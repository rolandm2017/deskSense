// Option 1: Event Delegation (Most Efficient)
// document.addEventListener(
//     "click",
//     (e: MouseEvent) => {
//         // Find the closest video title element
//         if (e.target && e.target instanceof Element) {
//             const titleElement = e.target.closest("h2, h3, h4, .title-class");

//             if (titleElement) {
//                 console.log("Clicked on:", titleElement.textContent);
//                 // Your tracking logic here
//             }
//         } else {
//             console.warn("Found no target");
//         }
//     },
//     true
// );

// Option 2: Hover-to-Register Pattern
// document.addEventListener(
//     "mouseover",
//     (e) => {
//         if (e.target && e.target instanceof Element) {
//             const titleElement = e.target.closest("h2, h3, h4, .video-title");

//             if (
//                 titleElement &&
//                 titleElement instanceof HTMLElement &&
//                 !titleElement.dataset.listenerAdded
//             ) {
//                 titleElement.addEventListener("click", handleTitleClick);
//                 titleElement.dataset.listenerAdded = "true";
//             }
//         } else {
//             console.warn("Found no target");
//         }
//     },
//     true
// );

function obtuseConsoleLog() {
    console.log("############");
    console.log("######6#####");
    console.log("#######5####");
    console.log("########4###");
    console.log("#########3##");
    console.log("##########2#");
    console.log("############");
}

console.log("Hi from roly");
console.log("The script loaded");
console.log("The script loaded");
console.log("The script loaded");
console.log("The script loaded");
console.log("The script loaded");
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

// Option (3) "ready, fire, aim"
// This will log every single click on the page
document.addEventListener(
    "click",
    (e) => {
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
    },
    true
); // Use capture phase to make sure we catch everything
//
