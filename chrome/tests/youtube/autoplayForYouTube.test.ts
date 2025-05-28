import { describe, expect, test, vi } from "vitest";

import { ViewingTracker, YouTubeViewing } from "../../src/videoCommon/visits";

import { ServerApi } from "../../src/api";

import { PlayPauseDispatch } from "../../src/backgroundUtil";

import { InputCaptureManager } from "../../src/inputLogger/inputCaptureManager";
import { replaceAllMethodsWithMocks } from "../helper";

describe("YouTube Autoplay", () => {
    const m = new InputCaptureManager({ enabled: false }, 10);

    test("If the play event occurs before the page event, it waits to be bundled together", () => {
        const server = new ServerApi("disable", m);
        replaceAllMethodsWithMocks(server);

        const watchPageReportingMock = vi.fn();
        server.youtube.sendYouTubeWatchPage = watchPageReportingMock;

        const tracker = new ViewingTracker(server);

        const dispatch = new PlayPauseDispatch(tracker);

        const testUrl = "https://www.youtube.com/watch?v=JpgiGi2epAs";
        const sender = {
            tab: { url: testUrl },
        } as chrome.runtime.MessageSender;

        dispatch.noteYouTubeAutoPlayEvent(sender);

        expect(tracker.autoplayWaiting).toBe(true);

        expect(server.youtube.sendYouTubeWatchPage).not.toBeCalled();
        expect(server.youtube.sendPlayEvent).not.toBeCalled();
        expect(server.youtube.sendPauseEvent).not.toBeCalled();

        const youTubeVisit = new YouTubeViewing(
            "JpgiGi2epAs",
            testUrl,
            "an American, in Turkey, speaking Portuguese for 5 minutes (CC)",
            "Elysse Davega",
            9000
        );

        tracker.setCurrent(youTubeVisit);
        tracker.markAutoplayEventWaiting();
        tracker.reportInitialLandOnWatchPage();

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
        const server = new ServerApi("disable", m);
        replaceAllMethodsWithMocks(server);

        const watchPageReportingMock = vi.fn();
        server.youtube.sendYouTubeWatchPage = watchPageReportingMock;

        const sendPlayEventMock = vi.fn();
        server.youtube.sendPlayEvent = sendPlayEventMock;

        const tracker = new ViewingTracker(server);

        const dispatch = new PlayPauseDispatch(tracker);

        const youTubeVisit = new YouTubeViewing(
            "JpgiGi2epAs",
            "www.youtube.com/watch?v=JpgiGi2epAs",
            "an American, in Turkey, speaking Portuguese for 5 minutes (CC)",
            "Elysse Davega",
            9000
        );

        tracker.setCurrent(youTubeVisit);
        tracker.reportInitialLandOnWatchPage();

        expect(tracker.autoplayWaiting).toBe(false);
        expect(tracker.mostRecentReport?.mediaTitle).toBe(
            youTubeVisit.mediaTitle
        );

        expect(server.youtube.sendYouTubeWatchPage).toHaveBeenCalledOnce();

        const testUrl = "https://www.youtube.com/watch?v=JpgiGi2epAs";
        const sender = {
            tab: { url: testUrl },
        } as chrome.runtime.MessageSender;

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
