// chrome/src/chromeGainsFocusListener.ts

/*

This script enables sending a Chrome event as soon as
the user alt-tabs into Chrome!

It handles specifically the case where the user tabs into
another program, and then back into Chrome.

Previously, Chrome didn't know to send a 
"new tab active" event.

*/

window.addEventListener("focus", () => {
    console.log("Window gained focus");
    chrome.runtime.sendMessage({
        event: "window_gained_focus",
        source: "chromeGainsFocusListener",
    });
});
