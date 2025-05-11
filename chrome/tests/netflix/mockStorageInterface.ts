import { vi } from "vitest";
import { StorageInterface } from "../../src/netflix/storageApi";

import { DayHistory, WatchHistory } from "../../src/netflix/historyTracker";

// storage/MockStorageApi.ts - For testing
export class MockStorageApi implements StorageInterface {
    private mockData: Map<string, any> = new Map();

    // Optional: Make methods mockable
    loadHistoryV2 = vi.fn(async (): Promise<{ watchHistory: WatchHistory }> => {
        return {
            watchHistory: this.mockData.get("watchHistory") || {},
        };
    });

    saveHistoryV2 = vi.fn(async (historyInput: WatchHistory): Promise<void> => {
        this.mockData.set("watchHistory", historyInput);
    });

    saveDay = vi.fn(async (day: DayHistory): Promise<void> => {
        Object.entries(day).forEach(([key, value]) => {
            this.mockData.set(key, value);
        });
    });

    readAll = vi.fn(async (): Promise<{ [key: string]: any }> => {
        const result = {};
        this.mockData.forEach((value, key) => {
            result[key] = value;
        });
        return result;
    });

    deleteSelected = vi.fn(async (dates: string[]): Promise<void> => {
        dates.forEach((date) => this.mockData.delete(date));
    });

    // Helper method for tests
    _setMockData(key: string, value: any) {
        this.mockData.set(key, value);
    }

    _clearMockData() {
        this.mockData.clear();
    }
}
