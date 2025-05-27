/// <reference types="chrome"/>
import { afterEach, beforeEach, describe, test, vi } from "vitest";
import { ServerApi } from "../../src/api";
import { getDomainFromUrlAndSubmit } from "../../src/backgroundUtil";
import { resetDependencies, setDependencies } from "../../src/dependencies";
import { ViewingTracker, YouTubeViewing } from "../../src/videoCommon/visits";
import { replaceAllMethodsWithMocks } from "../helper";

describe("Player state is preserved while using a different program", () => {
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

    test("The user alt-tabs to a different program, then alt-tabs back in, the state is there still", () => {
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
});
