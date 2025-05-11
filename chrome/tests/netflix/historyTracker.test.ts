import { describe, expect, test, vi } from "vitest";

import { WatchHistoryTracker } from "../../src/netflix/historyTracker";

import { MockStorageApi } from "./mockStorageInterface";

import { pretendPreexistingHistory } from "./mockData";

/*

// TODO: Confirm you can get a new entry into db,
// TODO: Confirm you can get n entries out of the db
// TODO: Confirm you can delete an entry
// TODO: Call it a day

*/

describe("WatchHistoryTracker", () => {
    test("addWatchEntry", async () => {
        const mockStorageApi = new MockStorageApi();
        mockStorageApi.readAll.mockReturnValueOnce(
            Promise.resolve(pretendPreexistingHistory)
        );
        const historyTracker = new WatchHistoryTracker(mockStorageApi);

        historyTracker.saveHistory = vi.fn();
        historyTracker.cleanupOldHistory = vi.fn();

        const videoId = "39084324";
        const showName = "Black Mirror";
        const url = "netflix.com/watch/39084324";

        await historyTracker.addWatchEntry(videoId, showName, url);

        const key = Object.keys(historyTracker.todayHistory)[0];
        const historyEntries = historyTracker.todayHistory[key];

        expect(historyEntries.length).toBe(1);
        expect(historyTracker.saveHistory).toBeCalled();
        expect(historyTracker.cleanupOldHistory).toBeCalled();
    });
});
