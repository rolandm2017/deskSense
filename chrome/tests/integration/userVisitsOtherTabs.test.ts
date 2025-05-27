/// <reference types="chrome"/>
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { ServerApi } from "../../src/api";
import { getDomainFromUrlAndSubmit } from "../../src/backgroundUtil";
import { resetDependencies, setDependencies } from "../../src/dependencies";
import { ViewingTracker, YouTubeViewing } from "../../src/videoCommon/visits";
import { replaceAllMethodsWithMocks } from "../helper";

describe("Player state is preserved while visiting a different tab", () => {
    const mockChromeApi = {
        executeScript: vi.fn(),
    };

    beforeEach(() => {
        // Set up mock dependencies for testing
        setDependencies({ chromeApi: mockChromeApi });

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

        tracker.handleAltTabReturn(tab);

        expect(server.youtube.sendAltTabReturn).toHaveBeenCalled();
    });
    test("The user tabs into a two different tabs, then returns, and the state is there still", () => {
        const server = new ServerApi("disable");
        replaceAllMethodsWithMocks(server);

        const tracker = new ViewingTracker(server);

        // Set up executeScript to return different channel names based on call order
        let callCount = 0;
        mockChromeApi.executeScript.mockImplementation((options, callback) => {
            callCount++;
            let channelName;

            if (callCount === 1) {
                channelName = "Third Tab's YouTube Channel"; // For the thirdTab
            } else {
                channelName = "Test Channel Name"; // Default for other calls
            }

            setTimeout(() => {
                callback([{ result: channelName }]);
            }, 0);
        });

        const tabId = 9000;
        const tabUrl = "www.youtube.com/watch?v=Pt2Pj3JZ9Ow";
        let videoId = "Pt2Pj3JZ9Ow";
        const channelName = "Piece of French";
        const mainTabTitle = "A Day in My Life in FRENCH (with subtitles)";
        const youTubeVisit = new YouTubeViewing(
            videoId,
            tabUrl,
            mainTabTitle,
            channelName,
            tabId
        );
        const initialTab = {
            url: tabUrl,
            id: tabId,
            title: mainTabTitle,
        } as chrome.tabs.Tab;
        // User starts the test by tabbing into the current tab:
        getDomainFromUrlAndSubmit(initialTab);
        // tracker.setCurrent(youTubeVisit);

        // Tab to a tab without a player in it:
        const secondTab = {
            url: "www.x.com",
            id: 9001,
            title: "It's What's Happening",
        } as chrome.tabs.Tab;
        getDomainFromUrlAndSubmit(secondTab);

        // Tab to a YouTube page that has paused media:
        const thirdTab = {
            url: "https://www.youtube.com/watch?v=JpgiGi2epAs",
            id: 9002,
            title: "an American, in Turkey, speaking Portuguese for 5 minutes (CC)",
        } as chrome.tabs.Tab;
        getDomainFromUrlAndSubmit(thirdTab);

        // Tab back to the original YouTube page:
    });

    test("The user closes a tab, so the tab is deleted from the cache", () => {
        const server = new ServerApi("disable");
        replaceAllMethodsWithMocks(server);

        const tracker = new ViewingTracker(server);
    });

    // TODO: When user closes a tab, it is deleted from the cache.
});
