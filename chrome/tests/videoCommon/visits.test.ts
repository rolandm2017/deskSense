import { describe, expect, test, vi } from "vitest";

import { ServerApi } from "../../src/api";

import {
    NetflixViewing,
    ViewingTracker,
    YouTubeViewing,
} from "../../src/videoCommon/visits";

import { replaceAllMethodsWithMocks } from "../helper";

// TODO:

// TODO: Test play/pause

describe("ViewingTracker", () => {
    //
    test("setCurrent sets the current media", () => {
        const server = new ServerApi();
        replaceAllMethodsWithMocks(server);
        const tracker = new ViewingTracker(server);
        const media = new NetflixViewing("23456", "Hilda", "paused");
        tracker.setCurrent(media);

        expect(tracker.currentMedia?.mediaTitle).toBe(media.mediaTitle);
    });
    test("setCurrent updates the current media", () => {
        const server = new ServerApi();
        replaceAllMethodsWithMocks(server);
        const tracker = new ViewingTracker(server);
        const media = new NetflixViewing("23456", "Hilda", "paused");
        tracker.setCurrent(media);

        const media2 = new NetflixViewing("9876", "Carmen San Diego", "paused");
        tracker.setCurrent(media2);

        expect(tracker.currentMedia).toBeInstanceOf(NetflixViewing);
        expect(tracker.currentMedia?.mediaTitle).toBe(media2.mediaTitle);
    });
    test("reportNetflixWatchPage sets a partial page info and calls an API", () => {
        const server = new ServerApi();
        replaceAllMethodsWithMocks(server);
        const tracker = new ViewingTracker(server);

        const target = "484848";
        tracker.reportNetflixWatchPage(target);

        expect(tracker.partialNetflixDescriptor).toBe(target);
    });
    test("reportYouTubeWatchPage calls an API", () => {
        const server = new ServerApi();
        replaceAllMethodsWithMocks(server);
        const tracker = new ViewingTracker(server);
        const youTubePage = new YouTubeViewing(
            "5959",
            "A Day of My Life In French!",
            "Piece of French"
        );
        tracker.setCurrent(youTubePage);

        tracker.reportYouTubeWatchPage();

        expect(server.youtube.reportYouTubePage).toHaveBeenCalledOnce();
        expect(server.netflix.reportNetflixPage).not.toHaveBeenCalledOnce();
    });
    test("markPlaying calls an API", () => {
        const server = new ServerApi();
        replaceAllMethodsWithMocks(server);
        const tracker = new ViewingTracker(server);
        const youTubePage = new YouTubeViewing(
            "5959",
            "A Day of My Life In French!",
            "Piece of French"
        );
        const convertToPayloadSpy = vi.spyOn(youTubePage, "convertToPayload");

        tracker.setCurrent(youTubePage);

        tracker.reportYouTubeWatchPage();

        tracker.markPlaying();

        expect(convertToPayloadSpy).toHaveBeenCalled();

        expect(server.youtube.sendPlayEvent).toHaveBeenCalledOnce();

        expect(server.netflix.sendPauseEvent).not.toHaveBeenCalled();
        expect(server.netflix.sendPlayEvent).not.toHaveBeenCalled();
    });
    test("markPaused calls an API", () => {
        const server = new ServerApi();
        replaceAllMethodsWithMocks(server);
        const tracker = new ViewingTracker(server);
        const youTubePage = new YouTubeViewing(
            "5959",
            "A Day of My Life In French!",
            "Piece of French"
        );
        const convertToPayloadSpy = vi.spyOn(youTubePage, "convertToPayload");

        tracker.setCurrent(youTubePage);
        tracker.reportYouTubeWatchPage();
        tracker.markPlaying();

        tracker.markPaused();

        expect(convertToPayloadSpy).toHaveBeenCalled();

        expect(server.youtube.sendPauseEvent).toHaveBeenCalledOnce();

        expect(server.netflix.sendPauseEvent).not.toHaveBeenCalled();
        expect(server.netflix.sendPlayEvent).not.toHaveBeenCalled();
    });
});
