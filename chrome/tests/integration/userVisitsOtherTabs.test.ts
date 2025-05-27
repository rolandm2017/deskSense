/// <reference types="chrome"/>
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { ServerApi } from "../../src/api";
import { distributeTaskData, getTaskForDomain } from "../../src/backgroundUtil";
import { taskTypes } from "../../src/const";
import { resetDependencies, setDependencies } from "../../src/dependencies";
import { Task } from "../../src/interface/interfaces";
import { ViewingTracker, YouTubeViewing } from "../../src/videoCommon/visits";
import { replaceAllMethodsWithMocks } from "../helper";

describe("Player state is preserved while visiting a different Chrome tab", () => {
    const mockChromeApi = {
        executeScript: vi.fn(),
    };

    beforeEach(() => {
        // Set up mock dependencies for testing
        setDependencies({ chromeApi: mockChromeApi, scrapeDelay: 0 });

        // Reset mocks
        vi.clearAllMocks();

        // Configure executeScript mock to simulate successful channel extraction
        mockChromeApi.executeScript.mockImplementation((options, callback) => {
            // Simulate the async nature with setTimeout
            setTimeout(() => {
                callback([{ result: "Test Channel Name" }]);
            }, 0);
        });
    });

    afterEach(() => {
        // Reset to production dependencies
        resetDependencies();
    });

    test("When the user opens a link in a new tab, the initial player state is fetched and set", () => {
        // Situation: User middle clicks to open a link in a new tab.
        // User switches to the tab. They have never visited before, because
        // they just opened it in a new tab using middle click.
        const server = new ServerApi("disable");
        replaceAllMethodsWithMocks(server);

        const tracker = new ViewingTracker(server);

        const tabUrl = "www.youtube.com/watch?v=Pt2Pj3JZ9Ow";
        const tabId = 9000;

        expect(tracker.hasPlayerStateForTab(tabId)).toBeFalsy();

        let videoId = "Pt2Pj3JZ9Ow";
        const channelName = "Piece of French";

        const youTubeVisit = new YouTubeViewing(
            videoId,
            tabUrl,
            "A Day in My Life in FRENCH (with subtitles)",
            channelName,
            tabId
        );
        tracker.setCurrent(youTubeVisit);

        expect(tracker.hasPlayerStateForTab(tabId)).toBeTruthy();
    });
    test("When the user tabs back to the tab, the player state is there ", () => {
        // Situation: The user opened a tab, watched for two min, tabs away with
        // the player playing. A moment passes. They tab back to the player page.
        // And the state is there!
        const server = new ServerApi("disable");
        replaceAllMethodsWithMocks(server);
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
        tracker.setCurrent(youTubeVisit);

        const tab = {
            id: tabId,
            url: "whatever",
        } as chrome.tabs.Tab;

        // FIXME: This IS NOT an alt tab return scenario
        // tracker.handleAltTabReturn(tab);

        // expect(server.youtube.sendAltTabReturn).toHaveBeenCalled();
    });

    // Helper function to promisify your callback-based function
    function getTaskForDomainAsync(
        tab: chrome.tabs.Tab,
        getTask: Function,
        tracker: ViewingTracker
    ): Promise<Task | undefined> {
        return new Promise((resolve) => {
            const syncResult = getTask(
                tab,
                (asyncTask) => {
                    resolve(asyncTask);
                },
                tracker
            );

            if (syncResult !== undefined) {
                resolve(syncResult);
            }
        });
    }

    test("The user tabs leaves the first tab, then returns, and the state doesn't need to be fetched again", async () => {
        const server = new ServerApi("disable");
        replaceAllMethodsWithMocks(server);

        const mockSendYouTubeWatchPage =
            vi.fn<
                (
                    tabTitle: string | undefined,
                    videoId: string,
                    channel: string,
                    initialPlayerState: "playing" | "paused"
                ) => void
            >();
        server.youtube.sendYouTubeWatchPage = mockSendYouTubeWatchPage;

        const tracker = new ViewingTracker(server);
        const useStoredPlayerStateSpy = vi.spyOn(
            tracker,
            "useStoredPlayerState"
        );
        const setCurrentSpy = vi.spyOn(tracker, "setCurrent");

        // Set up executeScript to return different channel names based on call order
        const pieceOfFrench = "Piece of French";

        let callCount = 0;
        mockChromeApi.executeScript.mockImplementation((options, callback) => {
            callCount++;
            let channelName;

            if (callCount === 0 || callCount == 3) {
                channelName = pieceOfFrench; // For the first and final tab
            } else {
                channelName = "Test Channel Name"; // Default for other calls
            }

            setTimeout(() => {
                callback([{ result: channelName }]);
            }, 0);
        });

        const tabId = 9000;
        const tabUrl = "https://www.youtube.com/watch?v=Pt2Pj3JZ9Ow";
        let videoId = "Pt2Pj3JZ9Ow";
        const mainTabTitle = "A Day in My Life in FRENCH (with subtitles)";

        const initialTab = {
            url: tabUrl,
            id: tabId,
            title: mainTabTitle,
        } as chrome.tabs.Tab;
        const secondTab = {
            url: "https://www.x.com",
            id: 9001,
            title: "It's What's Happening",
        } as chrome.tabs.Tab;
        const thirdTab = {
            url: "https://www.youtube.com/watch?v=JpgiGi2epAs",
            id: 9002,
            title: "an American, in Turkey, speaking Portuguese for 5 minutes (CC)",
        } as chrome.tabs.Tab;

        // User starts the test by tabbing into the current tab:
        const firstTask = await getTaskForDomainAsync(
            initialTab,
            getTaskForDomain,
            tracker
        );
        expect(firstTask?.type).toBe(taskTypes.YOUTUBE_WATCH_PAGE);
        distributeTaskData(firstTask, server, tracker);

        // FIXME: it needs to get the proper youtube Visit out of the script
        expect(tracker.currentMedia?.mediaTitle).toBe(mainTabTitle);
        expect(tracker.currentMedia?.videoId).toBe(videoId);
        expect(server.youtube.sendYouTubeWatchPage).toHaveBeenCalledOnce();

        tracker.markPlaying();

        expect(tracker.currentMedia?.playerState).toBe("playing");

        // check up on the cached value
        const v = tracker.stateCache.get(tabId);
        if (v instanceof YouTubeViewing) {
            expect(v).toBeInstanceOf(YouTubeViewing);
            expect(v.mediaTitle).toBe(initialTab.title);
            expect(v.playerState).toBe("playing");
        } else {
            throw new Error("not the right type");
        }

        // Tab to a tab without a player in it:
        const secondTask = await getTaskForDomainAsync(
            secondTab,
            getTaskForDomain,
            tracker
        );
        distributeTaskData(secondTask, server, tracker);

        // Tab to a YouTube page that has paused media:
        const thirdTask = await getTaskForDomainAsync(
            thirdTab,
            getTaskForDomain,
            tracker
        );
        distributeTaskData(thirdTask, server, tracker);

        /**
         * Look at what is not used at this point:
         */
        expect(useStoredPlayerStateSpy).not.toHaveBeenCalled();
        expect(server.youtube.sendYouTubeWatchPage).toHaveBeenCalledTimes(2);

        expect(tracker.currentMedia?.mediaTitle).toBe(thirdTab.title);
        expect(tracker.currentMedia?.playerState).toBe("paused");

        // User tabs back to the original YouTube page:
        const returnTask = await getTaskForDomainAsync(
            initialTab,
            getTaskForDomain,
            tracker
        );
        expect(firstTask?.type).toBe(taskTypes.YOUTUBE_WATCH_PAGE);
        distributeTaskData(returnTask, server, tracker);

        expect(setCurrentSpy).toBeCalledTimes(3);

        // Check that the tracker received the same object as before
        expect(useStoredPlayerStateSpy).toHaveBeenCalledOnce();
        expect(tracker.currentMedia?.mediaTitle).toBe(initialTab.title);
        expect(tracker.currentMedia?.playerState).toBe("playing");

        expect(server.youtube.sendYouTubeWatchPage).toHaveBeenCalledTimes(3);

        const payloadPlayerState1 = mockSendYouTubeWatchPage.mock.calls[0][3];
        const payloadPlayerState2 = mockSendYouTubeWatchPage.mock.calls[1][3];
        expect(payloadPlayerState1).toBe("paused");
        expect(payloadPlayerState2).toBe("paused");

        const payloadVideoId = mockSendYouTubeWatchPage.mock.calls[2][1];
        const payloadPlayerState = mockSendYouTubeWatchPage.mock.calls[2][3];

        console.log(mockSendYouTubeWatchPage.mock.calls.length, "length");

        expect(payloadVideoId).toBe(videoId);
        expect(payloadPlayerState).toBe("playing");
    });

    // test("The user closes a tab, so the tab is deleted from the cache", () => {
    //     const server = new ServerApi("disable");
    //     replaceAllMethodsWithMocks(server);

    //     const tracker = new ViewingTracker(server);
    // });

    // TODO: When user closes a tab, it is deleted from the cache.
});
