import { WatchEntry } from "./historyRecorder";

export interface StorageInterface {
    readWholeHistory(): Promise<WatchEntry[]>;
    saveAll(entries: WatchEntry[]): Promise<void>;
    saveDay(day: WatchEntry[]): Promise<void>;
    readAll(): Promise<WatchEntry[]>;
    deleteSelected(dates: string[]): Promise<void>;
}

class StorageApi implements StorageInterface {
    constructor() {
        //
    }

    async saveAll(entries: WatchEntry[]): Promise<void> {
        return new Promise((resolve) => {
            chrome.storage.local.set({ wholeHistory: entries }, () => {
                console.log("Saved all " + entries.length + "  entries");
                resolve();
            });
        });
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

    async readWholeHistory(): Promise<WatchEntry[]> {
        return new Promise((resolve) => {
            chrome.storage.local.get("wholeHistory", (result) => {
                // Convert the object to an array of DayHistory objects
                const savedEntries: WatchEntry[] = result.wholeHistory || [];
                console.log("all stored data:", savedEntries); // All stored data
                resolve(savedEntries);
            });
        });
    }

    async readAll(): Promise<WatchEntry[]> {
        console.log("In read all");
        return new Promise((resolve) => {
            chrome.storage.local.get(null, (result) => {
                console.log("all stored data:", result); // All stored data
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

    async deleteAll(safetySwitch?: boolean) {
        if (safetySwitch) {
            chrome.storage.local.clear(() => {
                console.log("Storage cleared completely!");
            });
        }
    }
}

export const storageApi = new StorageApi();
