import { describe, expect, test, vi } from "vitest";

import { ViewingTracker, YouTubeViewing } from "../../src/videoCommon/visits";

import {
    netflixUrl,
    ServerApi,
    youtubePlayerStateUrl,
    youTubeUrl,
} from "../../src/api";

describe("ViewingTracker and Server API", () => {
    test("reportNetflixWatchPage sets a partial page info and calls an API", () => {
        const server = new ServerApi();

        const payloadMock = vi.fn();
        server.replacePayloadMethod(payloadMock);

        const tracker = new ViewingTracker(server);

        const target = "484848";
        tracker.reportNetflixWatchPage(target);

        expect(tracker.partialNetflixDescriptor).toBe(target);

        const targetUrl = payloadMock.mock.calls[0][0];

        expect(targetUrl).toBe(netflixUrl);

        const deliverable = payloadMock.mock.calls[0][1];

        expect(deliverable.videoId).toBeDefined();
        expect(deliverable.videoId).toBe(target);
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

        const targetUrl = payloadMock.mock.calls[0][0];

        expect(targetUrl).toBe(youTubeUrl);

        const deliverable = payloadMock.mock.calls[0][1];

        expect(deliverable).toBeDefined();
        expect(deliverable.tabTitle).toBeDefined();
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

        const targetUrl = payloadMock.mock.calls[0][0];

        expect(targetUrl).toBe(youtubePlayerStateUrl);

        const deliverable = payloadMock.mock.calls[0][1];

        expect(deliverable).toBeDefined();
        expect(deliverable.tabTitle).toBeDefined();
        expect(deliverable.videoId).toBeDefined();
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

        const targetUrl = payloadMock.mock.calls[0][0];

        expect(targetUrl).toBe(youtubePlayerStateUrl);

        const deliverable = payloadMock.mock.calls[0][1];

        expect(deliverable).toBeDefined();
        expect(deliverable.tabTitle).toBeDefined();
        expect(deliverable.videoId).toBeDefined();
    });
});
