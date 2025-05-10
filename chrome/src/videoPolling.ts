// Note that this:
//             "run_at": "document_start"
// Would run way too early. As per Claude:
// """
// document_start - Chrome injects the script as soon as possible
// after the document element is created, but
// before any other DOM is constructed or loaded.
// """
// "document_end" is "after the DOM is complete but before subresources (images, etc.) finish loading."

function attachVideoListeners() {
    console.log("In attachVideoListeners");
    const video = document.querySelector("video");
    console.log(video, "video");
    if (!video) {
        setTimeout(attachVideoListeners, 1000);
        return;
    }
    console.log("Injecting video listeners");
    video.addEventListener("play", () => {
        console.log("Sending play message");
        chrome.runtime.sendMessage({ event: "play" });
    });

    video.addEventListener("pause", () => {
        console.log("Sending *pause message");
        chrome.runtime.sendMessage({ event: "pause" });
    });
}

attachVideoListeners();
