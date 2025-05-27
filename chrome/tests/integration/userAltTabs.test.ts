/// <reference types="chrome"/>
import { describe, expect, test, vi } from "vitest";
import { ServerApi } from "../../src/api";
import { handleUserTabsBackIn } from "../../src/backgroundUtil";
import { AltTabYouTubeReturn } from "../../src/interface/interfaces";
import { ViewingTracker, YouTubeViewing } from "../../src/videoCommon/visits";
import { replaceAllMethodsWithMocks } from "../helper";

describe("Player state is preserved while using a different program", () => {
    test("The user alt-tabs to a different program, then alt-tabs back in, the state is there still", () => {
        const server = new ServerApi("disable");
        replaceAllMethodsWithMocks(server);

        const sendAltTabReturnMock = vi.fn();
        server.youtube.sendAltTabReturn = sendAltTabReturnMock;

        const tracker = new ViewingTracker(server);

        const tabId = 9000;
        const tabUrl = "www.youtube.com/watch?v=Pt2Pj3JZ9Ow";
        let videoId = "Pt2Pj3JZ9Ow";
        const channelName = "Piece of French";
        const youTubeVisit = new YouTubeViewing(
            videoId,
            tabUrl,
            "A Day in My Life in FRENCH (with subtitles)",
            channelName,
            tabId
        );
        // Ext finishes handling arrival on page!
        let currentTabId = tabId;
        tracker.setCurrent(youTubeVisit);

        tracker.markPlaying();
        tracker.markPaused();
        tracker.markPlaying();

        // Unseen: USER ALT-TABS AWAY!

        // Some time passes

        // User tabs back in!
        const activeTab = { id: tabId, url: tabUrl } as chrome.tabs.Tab;
        handleUserTabsBackIn(tabUrl, activeTab, tracker);

        expect(server.youtube.sendAltTabReturn).toHaveBeenCalledOnce();

        const tabReturnPayload: AltTabYouTubeReturn =
            sendAltTabReturnMock.mock.calls[0][0];
        expect(tabReturnPayload).toBeDefined();
        expect(tabReturnPayload.channel).toBe(channelName);
        expect(tabReturnPayload.videoId).toBe(videoId);
        expect(tabReturnPayload.playerState).toBe("playing");

        // AND! It survives another alt tab:

        tracker.markPaused();

        // Unseen: USER ALT-TABS AWAY!

        // User tabs back in!
        handleUserTabsBackIn(tabUrl, activeTab, tracker);
        expect(server.youtube.sendAltTabReturn).toHaveBeenCalledTimes(2);

        const tabReturnPayload2: AltTabYouTubeReturn =
            sendAltTabReturnMock.mock.calls[1][0];
        expect(tabReturnPayload2).toBeDefined();
        expect(tabReturnPayload2.playerState).toBe("paused");
    });
});
