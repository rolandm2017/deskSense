/// <reference types="chrome"/>
import { afterEach, beforeEach, describe, test, vi } from "vitest";
import { ServerApi } from "../../src/api";
import { distributeTaskData, getTaskForDomain } from "../../src/backgroundUtil";
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

    // test("When the user opens a link in a new tab, the initial player state is fetched and set", () => {
    //     // Situation: User middle clicks to open a link in a new tab.
    //     // User switches to the tab. They have never visited before, because
    //     // they just opened it in a new tab using middle click.
    //     const server = new ServerApi("disable");
    //     replaceAllMethodsWithMocks(server);

    //     const tracker = new ViewingTracker(server);

    //     const tabUrl = "www.youtube.com/watch?v=Pt2Pj3JZ9Ow";
    //     const tabId = 9000;

    //     expect(tracker.hasPlayerStateForTab(tabId)).toBeFalsy();

    //     let videoId = "Pt2Pj3JZ9Ow";
    //     const channelName = "Piece of French";

    //     const youTubeVisit = new YouTubeViewing(
    //         videoId,
    //         tabUrl,
    //         "A Day in My Life in FRENCH (with subtitles)",
    //         channelName,
    //         tabId
    //     );
    //     tracker.setCurrent(youTubeVisit);

    //     expect(tracker.hasPlayerStateForTab(tabId)).toBeTruthy();
    // });
    // test("When the user tabs back to the tab, the player state is there ", () => {
    //     // Situation: The user opened a tab, watched for two min, tabs away with
    //     // the player playing. A moment passes. They tab back to the player page.
    //     // And the state is there!
    //     const server = new ServerApi("disable");
    //     replaceAllMethodsWithMocks(server);
    //     const tracker = new ViewingTracker(server);

    //     const tabId = 9000;
    //     const tabUrl = "www.youtube.com/watch?v=Pt2Pj3JZ9Ow";
    //     let videoId = "Pt2Pj3JZ9Ow";
    //     const channelName = "Piece of French";
    //     const youTubeVisit = new YouTubeViewing(
    //         videoId,
    //         tabUrl,
    //         "A Day in My Life in FRENCH (with subtitles)",
    //         channelName,
    //         tabId
    //     );
    //     tracker.setCurrent(youTubeVisit);

    //     const tab = {
    //         id: tabId,
    //         url: "whatever",
    //     } as chrome.tabs.Tab;

    //     // FIXME: This IS NOT an alt tab return scenario
    //     // tracker.handleAltTabReturn(tab);

    //     // expect(server.youtube.sendAltTabReturn).toHaveBeenCalled();
    // });

    // Helper function to promisify your callback-based function
    function getTaskForDomainAsync(
        tab: chrome.tabs.Tab,
        tracker: ViewingTracker
    ): Promise<Task | undefined> {
        return new Promise((resolve) => {
            const syncResult = getTaskForDomain(
                tab,
                (asyncTask) => {
                    console.log("HERE", asyncTask, "105ru");
                    resolve(asyncTask);
                },
                tracker
            );
            console.log(syncResult, "110ru");

            if (syncResult !== undefined) {
                resolve(syncResult);
            }
        });
    }

    test("The user tabs leaves the first tab, then returns, and the state doesn't need to be fetched again", async () => {
        const server = new ServerApi("disable");
        replaceAllMethodsWithMocks(server);

        const tracker = new ViewingTracker(server);

        const start = Date.now();
        const t1 = () =>
            console.log(`t1: ${((Date.now() - start) / 1000).toFixed(3)}s`);
        t1();

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
        const secondTab = {
            url: "www.x.com",
            id: 9001,
            title: "It's What's Happening",
        } as chrome.tabs.Tab;
        const thirdTab = {
            url: "https://www.youtube.com/watch?v=JpgiGi2epAs",
            id: 9002,
            title: "an American, in Turkey, speaking Portuguese for 5 minutes (CC)",
        } as chrome.tabs.Tab;
        const fourthTab = {
            url: "https://www.youtube.com/watch?v=dfsafdsafds",
            id: 9003,
            title: "Does This Run?",
        } as chrome.tabs.Tab;

        // User starts the test by tabbing into the current tab:
        const firstTask = await getTaskForDomainAsync(initialTab, tracker);
        distributeTaskData(firstTask, server, tracker);
        const t2 = () =>
            console.log(`t2: ${((Date.now() - start) / 1000).toFixed(3)}s`);
        t2();

        // Tab to a tab without a player in it:
        const secondTask = await getTaskForDomainAsync(secondTab, tracker);
        distributeTaskData(secondTask, server, tracker);
        const t3 = () =>
            console.log(`t3: ${((Date.now() - start) / 1000).toFixed(3)}s`);
        t3();

        // Tab to a YouTube page that has paused media:
        const thirdTask = await getTaskForDomainAsync(thirdTab, tracker);
        console.log(thirdTask, "third task 189ru");
        distributeTaskData(thirdTask, server, tracker);
        console.log(`t4: ${((Date.now() - start) / 1000).toFixed(3)}s`);

        console.log("second to last task");
        console.log("second to last task");
        console.log("second to last task");
        // User tabs back to the original YouTube page:
        const returnTask = await getTaskForDomainAsync(fourthTab, tracker);
        console.log(returnTask, "194ru");
        distributeTaskData(returnTask, server, tracker);
        console.log(`t5: ${((Date.now() - start) / 1000).toFixed(3)}s`);
        console.log("starting return to original page");
        console.log("starting return to original page");
        console.log("starting return to original page");
        const returnTask2 = await getTaskForDomainAsync(initialTab, tracker);
        console.log(returnTask2, "208ru");
        distributeTaskData(returnTask2, server, tracker);
    });

    // test("The user closes a tab, so the tab is deleted from the cache", () => {
    //     const server = new ServerApi("disable");
    //     replaceAllMethodsWithMocks(server);

    //     const tracker = new ViewingTracker(server);
    // });

    // TODO: When user closes a tab, it is deleted from the cache.
});
