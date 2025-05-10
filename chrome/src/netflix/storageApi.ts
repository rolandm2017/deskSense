import { DayHistory, WatchHistory } from "./history";

function loadHistory() {
    return new Promise((resolve) => {
        chrome.storage.local.get(["watchHistory"], (result) => {
            const currentHistory = result.watchHistory || {};
            console.log("Loaded history:", currentHistory);
            resolve(currentHistory);
        });
    });
}

// Save history to Chrome storage
function saveHistory(historyInput: WatchHistory): Promise<void> {
    return new Promise((resolve) => {
        chrome.storage.local.set({ watchHistory: historyInput }, () => {
            console.log("History saved");
            resolve();
        });
    });
}

export async function loadHistoryV2(): Promise<{ watchHistory: WatchHistory }> {
    return new Promise((resolve) => {
        chrome.storage.local.get(["watchHistory"], (result) => {
            const currentHistory = result.watchHistory || {};
            console.log("Loaded history:", currentHistory);
            // FIXME: it doesn't resolve
        });
    });
}

// Save history to Chrome storage
export async function saveHistoryV2(historyInput: WatchHistory): Promise<void> {
    return new Promise((resolve) => {
        chrome.storage.local.set({ watchHistory: historyInput }, () => {
            console.log("History saved");
            resolve();
        });
    });
}

// // // --
// // // --
// // // --

export async function saveDay(day: DayHistory): Promise<void> {
    return new Promise((resolve) => {
        chrome.storage.local.set(day, () => {
            console.log("Saved day: ", Object.keys(day)[0]);
            resolve();
        });
    });
}

export async function readDay(dayString: string): Promise<DayHistory> {
    return new Promise((resolve) => {
        chrome.storage.local.get([dayString], (result) => {
            resolve(result);
        });
    });
}

export async function readAll(): Promise<{ [key: string]: any }> {
    return new Promise((resolve) => {
        chrome.storage.local.get(null, (result) => {
            console.log(result); // All stored data
            resolve(result);
        });
    });
}

export async function deleteSelected(dates: string[]): Promise<void> {
    return new Promise((resolve) => {
        chrome.storage.local.remove(dates, () => {
            if (chrome.runtime.lastError) {
                console.error("Error removing keys:", chrome.runtime.lastError);
            } else {
                console.log("Keys removed.");
            }
            resolve();
        });
    });
}
