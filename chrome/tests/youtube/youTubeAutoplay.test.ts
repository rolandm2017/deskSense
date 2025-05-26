import { describe, expect, test, vi } from "vitest";

import { ViewingTracker, YouTubeViewing } from "../../src/videoCommon/visits";

import { ServerApi } from "../../src/api";

import { PlayPauseDispatch } from "../../src/backgroundUtil";

import { PlayerStateCache } from "../../src/playerStateCache";
import { replaceAllMethodsWithMocks } from "../helper";

describe("YouTube Autoplay", () => {
    test("If the play event occurs before the page event, it waits to be bundled together", () => {
        const server = new ServerApi("disable");
        replaceAllMethodsWithMocks(server);

        const watchPageReportingMock = vi.fn();
        server.youtube.sendYouTubeWatchPage = watchPageReportingMock;

        const cache = new PlayerStateCache();
        const tracker = new ViewingTracker(cache, server);

        const dispatch = new PlayPauseDispatch(tracker);

        const sender = {
            tab: { url: "https://www.youtube.com/watch?v=JpgiGi2epAs" },
        };

        dispatch.noteYouTubeAutoPlayEvent(sender);

        expect(tracker.autoplayWaiting).toBe(true);

        expect(server.youtube.sendYouTubeWatchPage).not.toBeCalled();
        expect(server.youtube.sendPlayEvent).not.toBeCalled();
        expect(server.youtube.sendPauseEvent).not.toBeCalled();

        const youTubeVisit = new YouTubeViewing(
            "JpgiGi2epAs",
            sender.tab.url,
            "an American, in Turkey, speaking Portuguese for 5 minutes (CC)",
            "Elysse Davega",
            9000
        );

        tracker.setCurrent(youTubeVisit);
        tracker.reportYouTubeWatchPage();

        expect(tracker.autoplayWaiting).toBe(false);
        expect(tracker.mostRecentReport?.mediaTitle).toBe(
            youTubeVisit.mediaTitle
        );

        expect(server.youtube.sendPauseEvent).not.toBeCalled();
        expect(server.youtube.sendPlayEvent).not.toBeCalled();

        expect(server.youtube.sendYouTubeWatchPage).toHaveBeenCalledOnce();

        const tabTitle = watchPageReportingMock.mock.calls[0][0];
        const videoId = watchPageReportingMock.mock.calls[0][1];
        const channel = watchPageReportingMock.mock.calls[0][2];
        const initialPlayerState = watchPageReportingMock.mock.calls[0][3];

        // tabTitle: string | undefined,
        // channel: string,
        // initialPlayerState: "playing" | "paused"

        expect(tabTitle).toBe(youTubeVisit.mediaTitle);
        expect(videoId).toBe(youTubeVisit.videoId);

        expect(channel).toBe(youTubeVisit.channelName);
        expect(initialPlayerState).toBe("playing");
    });
    test("If the page event occurs first, the Play event uses the same info", () => {
        const server = new ServerApi("disable");
        replaceAllMethodsWithMocks(server);

        const watchPageReportingMock = vi.fn();
        server.youtube.sendYouTubeWatchPage = watchPageReportingMock;

        const sendPlayEventMock = vi.fn();
        server.youtube.sendPlayEvent = sendPlayEventMock;

        const cache = new PlayerStateCache();
        const tracker = new ViewingTracker(cache, server);

        const dispatch = new PlayPauseDispatch(tracker);

        const youTubeVisit = new YouTubeViewing(
            "JpgiGi2epAs",
            "www.youtube.com/watch?v=JpgiGi2epAs",
            "an American, in Turkey, speaking Portuguese for 5 minutes (CC)",
            "Elysse Davega",
            9000
        );

        tracker.setCurrent(youTubeVisit);
        tracker.reportYouTubeWatchPage();

        expect(tracker.autoplayWaiting).toBe(false);
        expect(tracker.mostRecentReport?.mediaTitle).toBe(
            youTubeVisit.mediaTitle
        );

        expect(server.youtube.sendYouTubeWatchPage).toHaveBeenCalledOnce();

        const sender = {
            tab: { url: "https://www.youtube.com/watch?v=JpgiGi2epAs" },
        };

        dispatch.noteYouTubeAutoPlayEvent(sender);

        expect(tracker.autoplayWaiting).toBe(false);

        expect(server.youtube.sendPlayEvent).toBeCalled();

        expect(server.youtube.sendPauseEvent).not.toBeCalled();

        const payload = sendPlayEventMock.mock.calls[0][0];
        const tabTitle = payload.tabTitle;
        const channel = payload.channelName;
        const videoId = payload.videoId;

        expect(tabTitle).toBe(youTubeVisit.mediaTitle);

        expect(channel).toBe(youTubeVisit.channelName);
        expect(videoId).toBe(youTubeVisit.videoId);
    });
});
