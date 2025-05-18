import { describe, expect, test, vi } from "vitest";

import { ViewingTracker, YouTubeViewing } from "../../src/videoCommon/visits";

import { ServerApi } from "../../src/api";

describe("ViewingTracker and Server API", () => {
    test("reportNetflixWatchPage sets a partial page info and calls an API", () => {
        const payloadMock = vi.fn();
        ServerApi.prototype.sendPayload = payloadMock;

        const server = new ServerApi();

        const tracker = new ViewingTracker(server);

        const target = "484848";
        tracker.reportNetflixWatchPage(target);

        expect(tracker.partialNetflixDescriptor).toBe(target);
    });
    test("reportYouTubeWatchPage calls an API", () => {
        const server = new ServerApi();

        const payloadMock = vi.fn();
        server.replacePayloadMethod(payloadMock);

        const tracker = new ViewingTracker(server);
        const youTubePage = new YouTubeViewing(
            "5959",
            "A Day of My Life In French!",
            "Piece of French"
        );
        tracker.setCurrent(youTubePage);

        tracker.reportYouTubeWatchPage();

        expect(payloadMock).toHaveBeenCalledOnce();
    });
    test("markPlaying calls an API", () => {
        const server = new ServerApi();

        const payloadMock = vi.fn();
        server.replacePayloadMethod(payloadMock);

        const tracker = new ViewingTracker(server);
        const youTubePage = new YouTubeViewing(
            "5959",
            "A Day of My Life In French!",
            "Piece of French"
        );
        tracker.setCurrent(youTubePage);

        tracker.reportYouTubeWatchPage();

        payloadMock.mockClear();

        tracker.markPlaying();

        expect(payloadMock).toHaveBeenCalledOnce();
    });
    test("markPaused calls an API", () => {
        const server = new ServerApi();

        const payloadMock = vi.fn();
        server.replacePayloadMethod(payloadMock);

        const tracker = new ViewingTracker(server);
        const youTubePage = new YouTubeViewing(
            "5959",
            "A Day of My Life In French!",
            "Piece of French"
        );
        tracker.setCurrent(youTubePage);
        tracker.reportYouTubeWatchPage();
        tracker.markPlaying();

        payloadMock.mockClear();

        tracker.markPaused();

        expect(payloadMock).toHaveBeenCalledOnce();
    });
});
