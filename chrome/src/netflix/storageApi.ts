import { WatchEntry } from "./historyTracker";

export interface StorageInterface {
    saveDay(day: WatchEntry[]): Promise<void>;
    readAll(): Promise<WatchEntry[]>;
    deleteSelected(dates: string[]): Promise<void>;
}

class StorageApi implements StorageInterface {
    constructor() {
        //
    }

    async saveDay(day: WatchEntry[]): Promise<void> {
        return new Promise((resolve) => {
            chrome.storage.local.set(day, () => {
                console.log("Saved day: ", Object.keys(day)[0]);
                resolve();
            });
        });
    }

    async readDay(dayString: string): Promise<WatchEntry[]> {
        return new Promise((resolve) => {
            chrome.storage.local.get(null, (result) => {
                const savedDays: WatchEntry[] = Object.values(result);
                resolve(savedDays);
            });
        });
    }

    async readAll(): Promise<WatchEntry[]> {
        return new Promise((resolve) => {
            chrome.storage.local.get(null, (result) => {
                console.log(result); // All stored data
                // Convert the object to an array of DayHistory objects
                const savedDays: WatchEntry[] = Object.values(result);
                resolve(savedDays);
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
