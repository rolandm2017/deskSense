import { DayHistory } from "./historyTracker";

export interface StorageInterface {
    saveDay(day: DayHistory): Promise<void>;
    readAll(): Promise<DayHistory[]>;
    deleteSelected(dates: string[]): Promise<void>;
}

class StorageApi implements StorageInterface {
    constructor() {
        //
    }

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

    async readAll(): Promise<DayHistory[]> {
        return new Promise((resolve) => {
            chrome.storage.local.get(null, (result) => {
                console.log(result); // All stored data
                // Convert the object to an array of DayHistory objects
                const savedDays: DayHistory[] = Object.values(result);
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
