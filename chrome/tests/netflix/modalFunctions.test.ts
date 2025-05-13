import { describe, expect, test, vi } from "vitest";

import { HistoryRecorder, WatchEntry } from "../../src/netflix/historyRecorder";

import { MockStorageApi } from "./mockStorageInterface";

import { pretendPreexistingHistory } from "./mockData";

const entryOne: WatchEntry = {
    showName: "Hilda",
    videoId: "83u492384u32",
    url: "netflix.com/watch/3408932432",
    watchCount: 1,
    timestamp: new Date().toISOString(),
};
const entryTwo: WatchEntry = {
    showName: "Hilda Season 2",
    videoId: "jfa8fd3p9",
    url: "netflix.com/watch/58932450982",

    timestamp: new Date().toISOString(),
    watchCount: 2,
};

describe("[integration] The modal's key behaviors work", () => {
    //
    test("Seeing the top five results works", async () => {
        // Expect loading the modal to cause the db to .read_all() and
        // cobble together a top five.
        const mockStorageApi = new MockStorageApi();
        mockStorageApi.readAll.mockReturnValueOnce(
            Promise.resolve(pretendPreexistingHistory)
        );
        const historyRecorder = new HistoryRecorder(mockStorageApi);

        const topFiveResponse = await historyRecorder.getTopFive();
        expect(topFiveResponse.length).toBe(5);
    });
    test("Selecting a dropdown entry updates the db", async () => {
        const mockStorageApi = new MockStorageApi();

        mockStorageApi.saveDay = vi.fn();
        const historyRecorder = new HistoryRecorder(mockStorageApi);

        const videoId = "9423432";
        const showName = "Carmen San Diego";
        const url = "netflix.com/watch/85239432";
        // TODO: Make it have a day already, 2025-05-12

        await historyRecorder.addWatchEntry(videoId, showName, url);

        const todayAsHistoryKey = historyRecorder.getTodaysDate();

        expect(mockStorageApi.saveDay).toHaveBeenCalled();

        const [dayHistory] = mockStorageApi.saveDay.mock.calls[0];
        const key = Object.keys(dayHistory)[0];
        expect(key).toBe(todayAsHistoryKey);
        const value = dayHistory[key];
        expect(value.length).toBe(2);
    });
    test("Inputting a new title manually works", async () => {
        //
    });
    test("Loading the dropdown causes expired data to be deleted", async () => {
        const mockStorageApi = new MockStorageApi();
        mockStorageApi.readAll.mockReturnValueOnce(
            Promise.resolve(pretendPreexistingHistory)
        );
        const historyRecorder = new HistoryRecorder(mockStorageApi);
        historyRecorder.cleanupOldHistory = vi.fn();

        await historyRecorder.getTopFive();

        expect(historyRecorder.cleanupOldHistory).toHaveBeenCalled();
    });
});
