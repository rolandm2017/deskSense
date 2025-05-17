/*
 * This test documents that a Netflix show can have it's session started,
 * then played, paused, resumed, paused. Concluded.
 * And the server hears about all of it.
 */
import { describe, expect, test, vi } from "vitest";

import {
    HistoryRecorder,
    MessageRelay,
} from "../../../src/netflix/historyRecorder";
import { NetflixViewing } from "../../../src/videoCommon/visits";

import { MockStorageApi } from "../mockStorageInterface";

describe("The tracker works as intended for Netflix", () => {
    //
    function assertMocksNotCalled(arr) {
        for (const fn of arr) {
            expect(fn).not.toHaveBeenCalled();
        }
    }

    test("A currently active show has it's play event forwarded to the server", () => {
        const unused = new MockStorageApi();

        const relay = new MessageRelay();

        relay.alertTrackerOfNetflixPage = vi.fn();

        // Highly useful pattern for testing with mocks in TS
        const mockAlertTracker = vi.fn<(arg: NetflixViewing) => void>();
        relay.alertTrackerOfNetflixMediaInfo = mockAlertTracker;

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
            "playing"
        );

        //
        const netflixViewing = mockAlertTracker.mock.calls[0][0];
        expect(netflixViewing.mediaTitle).toBe(pretendShow.showName);
        expect(netflixViewing.videoId).toBe(pretendShow.urlId);
    });
});
