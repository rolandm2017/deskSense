/// <reference types="chrome"/>
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { taskTypes } from "../../src/const.ts";
import { resetDependencies, setDependencies } from "../../src/dependencies";
import { handleYouTubeUrl } from "../../src/youtube/youtube.ts";

describe("handleYouTubeUrl", () => {
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
                callback([{ result: "Base Test Channel Name" }]);
            }, 0);
        });
    });

    afterEach(() => {
        // Reset to production dependencies
        resetDependencies();
    });
    test("Watching a YouTube video returns a task with completed info", () => {
        const channelName = "Youtube Dot Test Dot Ts Channel";

        mockChromeApi.executeScript.mockImplementation((options, callback) => {
            setTimeout(() => {
                callback([{ result: channelName }]);
            }, 0);
        });

        const url = "https://www.youtube.com/watch?v=JpgiGi2epAs";
        const tab = { url: url, id: 9000, title: "Foo" } as chrome.tabs.Tab;

        const task = handleYouTubeUrl(tab);

        expect(task).toBeDefined();
        expect(task?.type).toBe(taskTypes.YOUTUBE_WATCH_PAGE);
    });
    test("The Channel page returns a Channel Page task with channel info", () => {
        const url = "https://www.youtube.com/@elyssedavega";
        const tab = { url: url, id: 9000, title: "Foo" } as chrome.tabs.Tab;

        const task = handleYouTubeUrl(tab);

        expect(task).toBeDefined();
        expect(task?.type).toBe(taskTypes.YOUTUBE_CHANNEL_PAGE);
    });
    test("All Shorts pages return the Shorts task type", () => {
        const url = "https://www.youtube.com/shorts/RCcTuGKg16U";
        const tab = { url: url, id: 9000, title: "Foo" } as chrome.tabs.Tab;

        const task = handleYouTubeUrl(tab);

        expect(task).toBeDefined();
        expect(task?.type).toBe(taskTypes.YOUTUBE_SHORTS);
    });
    test("Everything else is assumed to be the YouTube Home page", () => {
        //
        const exampleOne = "";
        const exampleTwo = "";
        const exampleThree = "";
    });
});
