import { describe, expect, test, vi } from "vitest";

import { HistoryRecorder } from "../../src/netflix/historyRecorder";

import { MockStorageApi } from "./mockStorageInterface";

import { pretendPreexistingHistory } from "./mockData";

/*

// TODO: Confirm you can get a new entry into db,
// TODO: Confirm you can get n entries out of the db
// TODO: Confirm you can delete an entry
// TODO: Call it a day

// TODO: get the first user input added in
// TODO: prove that a user input makes it to the "addEntryToDb" function
// TODO: 
// 

*/

describe("HistoryRecorder", () => {
    test("addWatchEntry", async () => {
        const mockStorageApi = new MockStorageApi();
        mockStorageApi.readAll.mockReturnValueOnce(
            Promise.resolve(pretendPreexistingHistory)
        );
        const historyRecorder = new HistoryRecorder(mockStorageApi);

        historyRecorder.saveHistory = vi.fn();
        historyRecorder.cleanupOldHistory = vi.fn();

        const videoId = "39084324";
        const showName = "Black Mirror";
        const url = "netflix.com/watch/39084324";

        await historyRecorder.addWatchEntry(videoId, showName, url);

        const key = Object.keys(historyRecorder.allHistory)[0];
        const historyEntries = historyRecorder.allHistory[key];

        expect(historyEntries.length).toBe(1);
        expect(historyRecorder.saveHistory).toBeCalled();
        expect(historyRecorder.cleanupOldHistory).toBeCalled();
    });
    test("The sorting function");
});
