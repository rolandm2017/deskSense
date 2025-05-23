import { describe, expect, test, vi } from "vitest";

import {
    HistoryRecorder,
    MessageRelay,
} from "../../src/netflix/historyRecorder";

import { NetflixViewing } from "../../src/videoCommon/visits";

import { MockStorageApi } from "./mockStorageInterface";

import { pretendPreexistingHistory } from "./mockData";

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
        relay.alertTrackerOfNetflixMediaInfo = mockAlertTracker;

        const historyRecorder = new HistoryRecorder(mockStorageApi, relay);
        historyRecorder.saveHistory = vi.fn();

        const showTitle = "Hilda";
        const url = "netflix.com/watch/1111112";
        const videoId = "1111112";

        historyRecorder.recordEnteredMediaTitle(showTitle, url, "playing");

        expect(relay.alertTrackerOfNetflixMediaInfo).toHaveBeenCalledOnce();

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
        relay.alertTrackerOfNetflixMediaInfo = vi.fn();
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
    test("The historyRecorder sends titles from new pages to the ViewingTracker via onMessage", () => {
        const unused = new MockStorageApi();

        const relay = new MessageRelay();

        const mockOnPageLoad =
            vi.fn<(fullUrl: string, videoId: string) => void>();
        relay.alertTrackerOfNetflixPage = mockOnPageLoad;

        // Highly useful pattern for testing with mocks in TS
        const mockOnViewing = vi.fn<(arg: NetflixViewing) => void>();
        relay.alertTrackerOfNetflixMediaInfo = mockOnViewing;

        const tracker = new HistoryRecorder(unused, relay);

        const pretendShow = {
            urlId: "2345",
            showName: "Hilda",
            url: "netflix.com/watch/2345",
        };
        tracker.sendPageDetailsToViewingTracker(pretendShow.url);
        tracker.recordEnteredMediaTitle(
            pretendShow.showName,
            pretendShow.url,
            "paused"
        );

        const args = mockOnPageLoad.mock.calls[0];
        console.log(args);

        const fullUrl = args[0];
        const videoId = args[1];
        expect(fullUrl).toBe(pretendShow.url);
        expect(videoId).toBe(pretendShow.urlId);
    });
});
