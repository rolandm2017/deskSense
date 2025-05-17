import { describe, expect, test, vi } from "vitest";

import {
    HistoryRecorder,
    MessageRelay,
} from "../../../src/netflix/historyRecorder";

import { WatchEntry } from "../../../src/interface/interfaces";
import { NetflixViewing } from "../../../src/videoCommon/visits";

import { MockStorageApi } from "../mockStorageInterface";

import { pretendPreexistingHistory } from "../mockData";

describe("[integration] The modal's key behaviors work", () => {
    //
    test("Seeing the top five results works", async () => {
        // Expect loading the modal to cause the db to .read_all() and
        // cobble together a top five.
        const mockStorageApi = new MockStorageApi();
        mockStorageApi.readWholeHistory.mockReturnValueOnce(
            Promise.resolve(pretendPreexistingHistory)
        );

        const relay = new MessageRelay();

        relay.alertTrackerOfNetflixPage = vi.fn();

        // Highly useful pattern for testing with mocks in TS
        const mockAlertTracker = vi.fn<(arg: NetflixViewing) => void>();
        relay.alertTrackerOfNetflixMediaInfo = mockAlertTracker;

        const historyRecorder = new HistoryRecorder(mockStorageApi, relay);

        const topFiveResponse = await historyRecorder.getTopFive();
        expect(topFiveResponse.length).toBe(5);
    });
    test("Selecting a dropdown entry updates the db", async () => {
        const mockStorageApi = new MockStorageApi();

        // Highly useful pattern for testing with mocks in TS
        const mockSaveAll = vi.fn<(arg: WatchEntry[]) => void>();
        mockStorageApi.saveAll = mockSaveAll;

        const relay = new MessageRelay();

        relay.alertTrackerOfNetflixPage = vi.fn();

        // Highly useful pattern for testing with mocks in TS
        const mockAlertTracker = vi.fn<(arg: NetflixViewing) => void>();
        relay.alertTrackerOfNetflixMediaInfo = mockAlertTracker;

        const historyRecorder = new HistoryRecorder(mockStorageApi, relay);

        const urlId = "85239432";
        const showName = "Carmen San Diego";
        const url = "netflix.com/watch/85239432";

        historyRecorder.recordEnteredMediaTitle(showName, url, "paused");

        expect(mockStorageApi.saveAll).toHaveBeenCalledOnce();

        const arrayOfWatchEntries = mockSaveAll.mock.calls[0][0];

        expect(arrayOfWatchEntries.length).toBeGreaterThan(0);
        expect(arrayOfWatchEntries[0].showName).toBe(showName);
        expect(arrayOfWatchEntries[0].url).toBe(url);
        expect(arrayOfWatchEntries[0].urlId).toBe(urlId);
    });
    // test("Inputting a new title manually works", async () => {
    //     // TODO
    // });
    test("Loading the dropdown causes expired data to be deleted", async () => {
        const mockStorageApi = new MockStorageApi();
        mockStorageApi.readAll.mockReturnValueOnce(
            Promise.resolve(pretendPreexistingHistory)
        );

        const relay = new MessageRelay();

        relay.alertTrackerOfNetflixPage = vi.fn();

        // Highly useful pattern for testing with mocks in TS
        const mockAlertTracker = vi.fn<(arg: NetflixViewing) => void>();
        relay.alertTrackerOfNetflixMediaInfo = mockAlertTracker;

        const historyRecorder = new HistoryRecorder(mockStorageApi, relay);
        historyRecorder.cleanupOldHistory = vi.fn();

        await historyRecorder.loadDropdown();

        expect(historyRecorder.cleanupOldHistory).toHaveBeenCalled();
    });
});
