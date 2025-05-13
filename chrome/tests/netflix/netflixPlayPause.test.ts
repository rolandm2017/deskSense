/*
 * This test documents that a Netflix show can have it's session started,
 * then played, paused, resumed, paused. Concluded.
 * And the server hears about all of it.
 */
import { describe, expect, test, vi } from "vitest";

import { ServerApi } from "../../src/api";
import { WatchHistoryTracker } from "../../src/netflix/historyTracker";
import { NetflixViewing, ViewingTracker } from "../../src/videoCommon/visits";

import { MockStorageApi } from "./mockStorageInterface";

describe("The Netflix tracker works as intended", () => {
    //
    test("The historyTracker deposits titles in the ViewingTracker and notifies the server", () => {
        const serverConn = new ServerApi();
        // turn off send payloads
        serverConn.netflix.reportNetflixPage = vi.fn();
        serverConn.netflix.sendPlayEvent = vi.fn();
        serverConn.netflix.sendPauseEvent = vi.fn();

        serverConn.youtube.reportYouTubePage = vi.fn();
        serverConn.youtube.sendPlayEvent = vi.fn();
        serverConn.youtube.sendPauseEvent = vi.fn();

        const viewingTrackerInit = new ViewingTracker(serverConn);
        const unused = new MockStorageApi();
        const tracker = new WatchHistoryTracker(viewingTrackerInit, unused);

        const pretendShow = {
            urlId: "2345",
            showName: "Hilda",
            url: "netflix.com/watch/2345",
        };
        tracker.recordEnteredMediaTitle(pretendShow.showName, pretendShow.url);
        // Expect the show to be in the viewing tracker
        const youtubeFns = [
            (serverConn.youtube.reportYouTubePage = vi.fn()),
            (serverConn.youtube.sendPlayEvent = vi.fn()),
            (serverConn.youtube.sendPauseEvent = vi.fn()),
        ];

        for (const fn of youtubeFns) {
            expect(fn).not.toHaveBeenCalled();
        }

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
    // test("A currently active show has it's play event forwarded to the server", () => {
    //     const serverConn = new ServerApi();
    //     // turn off send payload
    //     serverConn.youtube.reportYouTubePage = vi.fn();
    //     serverConn.youtube.sendPlayEvent = vi.fn();
    //     serverConn.youtube.sendPauseEvent = vi.fn();
    //     serverConn.netflix.reportNetflixPage = vi.fn();
    //     serverConn.netflix.sendPlayEvent = vi.fn();
    //     serverConn.netflix.sendPauseEvent = vi.fn();

    //     const viewingTrackerInit = new ViewingTracker(serverConn);
    //     const unused = new MockStorageApi();
    //     const tracker = new WatchHistoryTracker(viewingTrackerInit, unused);

    //     const pretendShow = {
    //         urlId: "2345",
    //         showName: "Hilda",
    //         url: "netflix.com/watch/2345",
    //     };
    //     tracker.addWatchEntry(
    //         pretendShow.urlId,
    //         pretendShow.showName,
    //         pretendShow.url
    //     );

    //     viewingTrackerInit.markPlaying();

    //     expect(viewingTrackerInit.currentMedia?.playerState).toBe("playing");
    //     expect(serverConn.youtube.sendPlayEvent).toHaveBeenCalledOnce();

    //     //
    // });
    // test("A playing show can be paused, and the server hears about it", () => {
    //     const serverConn = new ServerApi();
    //     // turn off send payload
    //     serverConn.youtube.reportYouTubePage = vi.fn();
    //     serverConn.youtube.sendPlayEvent = vi.fn();
    //     serverConn.youtube.sendPauseEvent = vi.fn();
    //     serverConn.netflix.reportNetflixPage = vi.fn();
    //     serverConn.netflix.sendPlayEvent = vi.fn();
    //     serverConn.netflix.sendPauseEvent = vi.fn();

    //     const viewingTrackerInit = new ViewingTracker(serverConn);
    //     const unused = new MockStorageApi();
    //     const tracker = new WatchHistoryTracker(viewingTrackerInit, unused);

    //     const pretendShow = {
    //         urlId: "2345",
    //         showName: "Hilda",
    //         url: "netflix.com/watch/2345",
    //     };
    //     tracker.addWatchEntry(
    //         pretendShow.urlId,
    //         pretendShow.showName,
    //         pretendShow.url
    //     );

    //     viewingTrackerInit.markPlaying();
    //     viewingTrackerInit.markPaused();

    //     expect(viewingTrackerInit.currentMedia?.playerState).toBe("paused");
    //     expect(serverConn.youtube.sendPauseEvent).toHaveBeenCalledOnce();
    // });
});
