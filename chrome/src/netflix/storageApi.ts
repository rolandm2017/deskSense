import { DayHistory, WatchHistory } from "./historyTracker";

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

export interface StorageInterface {
    loadHistoryV2(): Promise<{ watchHistory: WatchHistory }>;
    saveHistoryV2(historyInput: WatchHistory): Promise<void>;
    saveDay(day: DayHistory): Promise<void>;
    readAll(): Promise<{ [key: string]: any }>;
    deleteSelected(dates: string[]): Promise<void>;
}

class StorageApi implements StorageInterface {
    constructor() {
        //
    }
    async loadHistoryV2(): Promise<{ watchHistory: WatchHistory }> {
        return new Promise((resolve) => {
            chrome.storage.local.get(["watchHistory"], (result) => {
                const currentHistory = result.watchHistory || {};
                console.log("Loaded history:", currentHistory);
                // FIXME: it doesn't resolve
            });
        });
    }

    // Save history to Chrome storage
    async saveHistoryV2(historyInput: WatchHistory): Promise<void> {
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

    async saveDay(day: DayHistory): Promise<void> {
        return new Promise((resolve) => {
            chrome.storage.local.set(day, () => {
                console.log("Saved day: ", Object.keys(day)[0]);
                resolve();
            });
        });
    }

    async readDay(dayString: string): Promise<DayHistory> {
        return new Promise((resolve) => {
            chrome.storage.local.get([dayString], (result) => {
                resolve(result);
            });
        });
    }

    async readAll(): Promise<{ [key: string]: any }> {
        return new Promise((resolve) => {
            chrome.storage.local.get(null, (result) => {
                console.log(result); // All stored data
                resolve(result);
            });
        });
    }

    async deleteSelected(dates: string[]): Promise<void> {
        return new Promise((resolve) => {
            chrome.storage.local.remove(dates, () => {
                if (chrome.runtime.lastError) {
                    console.error(
                        "Error removing keys:",
                        chrome.runtime.lastError
                    );
                } else {
                    console.log("Keys removed.");
                }
                resolve();
            });
        });
    }
}

export const storageApi = new StorageApi();
