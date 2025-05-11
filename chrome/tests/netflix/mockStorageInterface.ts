import { vi } from "vitest";
import { StorageInterface } from "../../src/netflix/storageApi";

import { WatchEntry } from "../../src/netflix/historyTracker";

// storage/MockStorageApi.ts - For testing
export class MockStorageApi implements StorageInterface {
    private mockData: Map<string, any> = new Map();

    // Optional: Make methods mockable

    readWholeHistory = vi.fn(async (): Promise<WatchEntry[]> => {
        const result = [];
        this.mockData.forEach(([key, value]) => {
            this.mockData.set(key, value);
        });
        return result;
    });

    saveAll = vi.fn(async (entries: WatchEntry[]): Promise<void> => {
        Object.entries(entries).forEach(([key, value]) => {
            this.mockData.set(key, value);
        });
    });

    saveDay = vi.fn(async (day: WatchEntry[]): Promise<void> => {
        Object.entries(day).forEach(([key, value]) => {
            this.mockData.set(key, value);
        });
    });

    readAll = vi.fn(async (): Promise<WatchEntry[]> => {
        const result = [];
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
