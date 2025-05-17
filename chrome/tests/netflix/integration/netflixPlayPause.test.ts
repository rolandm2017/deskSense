/*
 * This test documents that a Netflix show can have it's session started,
 * then played, paused, resumed, paused. Concluded.
 * And the server hears about all of it.
 */
import { describe, expect, test, vi } from "vitest";

import { ServerApi } from "../../../src/api";
import { HistoryRecorder } from "../../../src/netflix/historyRecorder";
import {
    NetflixViewing,
    ViewingTracker,
} from "../../../src/videoCommon/visits";

import { MockStorageApi } from "../mockStorageInterface";

import { replaceAllMethodsWithMocks } from "../../helper";

describe("The tracker works as intended for Netflix", () => {
    //
    function assertMocksNotCalled(arr) {
        for (const fn of arr) {
            expect(fn).not.toHaveBeenCalled();
        }
    }
    test("The historyRecorder deposits titles in the ViewingTracker and notifies the server", () => {
        const serverConn = new ServerApi();
        // turn off send payloads
        replaceAllMethodsWithMocks(serverConn);

        const viewingTrackerInit = new ViewingTracker(serverConn);
        const unused = new MockStorageApi();
        const tracker = new HistoryRecorder(viewingTrackerInit, unused);

        const pretendShow = {
            urlId: "2345",
            showName: "Hilda",
            url: "netflix.com/watch/2345",
        };
        tracker.sendPageDetailsToViewingTracker(pretendShow.url);
        tracker.recordEnteredMediaTitle(pretendShow.showName, pretendShow.url);
        // Expect the show to be in the viewing tracker
        assertMocksNotCalled([
            (serverConn.youtube.reportYouTubePage = vi.fn()),
            (serverConn.youtube.sendPlayEvent = vi.fn()),
            (serverConn.youtube.sendPauseEvent = vi.fn()),
        ]);

        const media = viewingTrackerInit.currentMedia;
        expect(media).toBeDefined();
        expect(media).toBeInstanceOf(NetflixViewing);
        expect(media).toMatchObject({
            videoId: expect.any(String),
            mediaTitle: expect.any(String),
            timestamps: expect.any(Array),
            playerState: expect.stringMatching("paused"),
        });
        expect(viewingTrackerInit.currentMedia?.playerState).toBe("paused");
        // Expect the viewing tracker to have sent a server message:
        // tracker.netflix.reportNewPage().wasCalled()
        expect(serverConn.netflix.reportNetflixPage).toHaveBeenCalledOnce();
    });
    test("A currently active show has it's play event forwarded to the server", () => {
        const serverConn = new ServerApi();
        // turn off send payload
        replaceAllMethodsWithMocks(serverConn);

        const viewingTrackerInit = new ViewingTracker(serverConn);
        const unused = new MockStorageApi();
        const tracker = new HistoryRecorder(viewingTrackerInit, unused);

        const pretendShow = {
            urlId: "2345",
            showName: "Hilda",
            url: "netflix.com/watch/2345",
        };
        tracker.sendPageDetailsToViewingTracker(pretendShow.url);
        tracker.recordEnteredMediaTitle(pretendShow.showName, pretendShow.url);

        viewingTrackerInit.markPlaying();

        assertMocksNotCalled([
            (serverConn.youtube.reportYouTubePage = vi.fn()),
            (serverConn.youtube.sendPlayEvent = vi.fn()),
            (serverConn.youtube.sendPauseEvent = vi.fn()),
        ]);

        expect(viewingTrackerInit.currentMedia).toBeDefined();
        expect(viewingTrackerInit.currentMedia?.playerState).toBe("playing");
        expect(serverConn.netflix.sendPlayEvent).toHaveBeenCalledOnce();

        //
    });
    test("A playing show can be paused, and the server hears about it", () => {
        const serverConn = new ServerApi();
        // turn off send payload
        replaceAllMethodsWithMocks(serverConn);

        const viewingTrackerInit = new ViewingTracker(serverConn);
        const unused = new MockStorageApi();
        const tracker = new HistoryRecorder(viewingTrackerInit, unused);

        const pretendShow = {
            urlId: "2345",
            showName: "Hilda",
            url: "netflix.com/watch/2345",
        };
        tracker.sendPageDetailsToViewingTracker(pretendShow.url);

        tracker.recordEnteredMediaTitle(pretendShow.showName, pretendShow.url);

        viewingTrackerInit.markPlaying();
        viewingTrackerInit.markPaused();

        assertMocksNotCalled([
            (serverConn.youtube.reportYouTubePage = vi.fn()),
            (serverConn.youtube.sendPlayEvent = vi.fn()),
            (serverConn.youtube.sendPauseEvent = vi.fn()),
        ]);

        expect(viewingTrackerInit.currentMedia).toBeDefined();

        expect(viewingTrackerInit.currentMedia?.playerState).toBe("paused");
        expect(serverConn.netflix.sendPauseEvent).toHaveBeenCalledOnce();
    });
});
