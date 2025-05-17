import { describe, expect, test, vi } from "vitest";

import {
    HistoryRecorder,
    MessageRelay,
} from "../../src/netflix/historyRecorder";

import { NetflixViewing } from "../../src/videoCommon/visits";

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
    test("recordEnteredMediaTitle", () => {
        const mockStorageApi = new MockStorageApi();
        mockStorageApi.readAll.mockReturnValueOnce(
            Promise.resolve(pretendPreexistingHistory)
        );

        const relay = new MessageRelay();
        relay.alertTrackerOfNetflixPage = vi.fn();

        // Highly useful pattern for testing with mocks in TS
        const mockAlertTracker = vi.fn<(arg: NetflixViewing) => void>();
        relay.alertTrackerOfNetflixViewing = mockAlertTracker;

        const historyRecorder = new HistoryRecorder(mockStorageApi, relay);
        historyRecorder.saveHistory = vi.fn();

        const showTitle = "Hilda";
        const url = "netflix.com/watch/1111112";
        const videoId = "1111112";

        historyRecorder.recordEnteredMediaTitle(showTitle, url, "playing");

        expect(relay.alertTrackerOfNetflixViewing).toHaveBeenCalledOnce();

        expect(mockAlertTracker).toHaveBeenCalledOnce();
        const firstArgument = mockAlertTracker.mock.calls[0][0];
        expect(firstArgument.mediaTitle).toBe(showTitle);
        expect(firstArgument.videoId).toBe(videoId);

        expect(historyRecorder.saveHistory).toHaveBeenCalledOnce();
    });
    test("addWatchEntry", async () => {
        const mockStorageApi = new MockStorageApi();
        mockStorageApi.readAll.mockReturnValueOnce(
            Promise.resolve(pretendPreexistingHistory)
        );

        const relay = new MessageRelay();
        relay.alertTrackerOfNetflixPage = vi.fn();
        relay.alertTrackerOfNetflixViewing = vi.fn();
        const historyRecorder = new HistoryRecorder(mockStorageApi, relay);

        historyRecorder.saveHistory = vi.fn();
        historyRecorder.cleanupOldHistory = vi.fn();

        // test setup conditions
        expect(historyRecorder.allHistory.length).toBe(0);

        const videoId = "39084324";
        const showName = "Black Mirror";
        const url = "netflix.com/watch/39084324";

        const result = historyRecorder.addWatchEntry(videoId, showName, url);

        expect(historyRecorder.allHistory.length).toBe(1);

        expect(result).toBeDefined();
        expect(result.showName).toBe(showName);
    });
});
