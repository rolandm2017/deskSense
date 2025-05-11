export function recordEnteredValue(mediaTitle: string) {
    chrome.storage.local.set({ currentWatching: mediaTitle }, () => {
        console.log("Confirmed:", mediaTitle);
    });
}

export function handleIgnoreUrl(currentUrl: string) {
    chrome.storage.local.get(["ignoredVideos"], (result) => {
        const ignoredVideos = result.ignoredVideos || [];
        ignoredVideos.push(currentUrl);
        chrome.storage.local.set({ ignoredVideos }, () => {
            console.log("Ignored this video:", currentUrl);
        });
    });
}
