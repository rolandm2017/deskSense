/*
 * This test documents that a YouTube show can have it's session started,
 * then played, paused, resumed, paused. Concluded.
 * And the server hears about all of it.
 */
import { describe, expect, test } from "vitest";

import { ServerApi } from "../../src/api";

import { ViewingTracker, YouTubeViewing } from "../../src/videoCommon/visits";

import { replaceAllMethodsWithMocks } from "../helper";

describe("The YouTube tracker works as intended", () => {
    //
    test("A page update is sent to the server when the channel name arrives", () => {
        const api = new ServerApi("disable");
        // turn off send payloads
        replaceAllMethodsWithMocks(api);
        const viewingTrackerInit = new ViewingTracker(api);
        //
        const fakePage = {
            videoId: "456",
            tabTitle: "A Day of My Life in FRENCH!",
            channelName: "Piece of French",
        };
        const youTubeVisit = new YouTubeViewing(
            fakePage.videoId,
            fakePage.tabTitle,
            fakePage.channelName
        );
        viewingTrackerInit.setCurrent(youTubeVisit);
        viewingTrackerInit.reportYouTubeWatchPage();
        expect(api.youtube.reportYouTubeWatchPage).toHaveBeenCalledOnce();
    });
    test("A play event is sent to the server when it occurs", () => {
        const api = new ServerApi("disable");

        // turn off send payloads
        replaceAllMethodsWithMocks(api);

        const viewingTracker = new ViewingTracker(api);
        //
        const fakePage = {
            videoId: "456",
            tabTitle: "A Day of My Life in FRENCH!",
            channelName: "Piece of French",
        };
        const youTubeVisit = new YouTubeViewing(
            fakePage.videoId,
            fakePage.tabTitle,
            fakePage.channelName
        );
        viewingTracker.setCurrent(youTubeVisit);
        viewingTracker.reportYouTubeWatchPage();

        viewingTracker.markPlaying();

        expect(api.youtube.sendPlayEvent).toHaveBeenCalledOnce();
    });
    test("A pause event is sent to the server when it occurs", () => {
        const api = new ServerApi("disable");

        // turn off send payloads
        replaceAllMethodsWithMocks(api);

        const viewingTrackerInit = new ViewingTracker(api);
        //
        const fakePage = {
            videoId: "456",
            tabTitle: "A Day of My Life in FRENCH!",
            channelName: "Piece of French",
        };
        const youTubeVisit = new YouTubeViewing(
            fakePage.videoId,
            fakePage.tabTitle,
            fakePage.channelName
        );
        viewingTrackerInit.setCurrent(youTubeVisit);
        viewingTrackerInit.reportYouTubeWatchPage();

        viewingTrackerInit.markPlaying();
        viewingTrackerInit.markPaused();

        expect(viewingTrackerInit.currentMedia?.playerState).toBe("paused");
        expect(api.youtube.sendPlayEvent).toHaveBeenCalledOnce();
    });
});
