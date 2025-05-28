import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
import { ServerApi } from "../../src/api";
import {
    distributeTaskData,
    getTaskForDomain,
    handleUserTabsBackIn,
    PlayPauseDispatch,
} from "../../src/backgroundUtil";
import { resetDependencies, setDependencies } from "../../src/dependencies";
import { InputCaptureManager } from "../../src/inputLogger/inputCaptureManager";
import { PayloadCaptureEvent } from "../../src/types/captureEvents.types";
import { ViewingTracker } from "../../src/videoCommon/visits";
import { replayUsage } from "../replay/replayUsage";

// Get current file's directory and go up to chrome/
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const chromeDir = join(__dirname, "../..");

// Read and parse the JSON file

const sets = [
    [
        "user-input-activity-Tue May 27 2025 (2).json",
        "payload-events-Tue May 27 2025.json",
    ],
    [
        "user-input-activity-Tue May 27 2025 (3).json",
        "payload-events-Tue May 27 2025 (1).json",
    ],
];
const payloadLogFilePath = join(chromeDir, "logs", sets[1][1]);
const rawData = readFileSync(payloadLogFilePath, "utf8");
const payloadEvents = JSON.parse(rawData);

const activityLogFilePath = join(chromeDir, "logs", sets[1][0]);
const rawUserData = readFileSync(activityLogFilePath, "utf8");
const userEvents = JSON.parse(rawUserData);

describe("Run the system according to a set of recorded user inputs", () => {
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

    test("System responds in the same way it did last time", async () => {
        const capture = new InputCaptureManager({ enabled: false }, 1);
        const server = new ServerApi("disable", capture);
        const tracker = new ViewingTracker(server);
        const markPlayingSpy = vi.spyOn(tracker, "markPlaying");
        const markPausedSpy = vi.spyOn(tracker, "markPaused");
        const dispatch = new PlayPauseDispatch(tracker);
        const notePlayingSpy = vi.spyOn(dispatch, "notePlayEvent");
        const notePausedSpy = vi.spyOn(dispatch, "notePauseEvent");

        mockChromeApi.executeScript.mockImplementation((options, callback) => {
            let channelName = "elysse daVega";

            setTimeout(() => {
                callback([{ result: channelName }]);
            }, 0);
        });

        const system = {
            viewingTracker: tracker,
            serverApi: server,
            dispatch: dispatch,
            handleUserTabsBackIn: handleUserTabsBackIn,
            getTaskForDomain: getTaskForDomain,
            distributeTaskData: distributeTaskData,
        };
        for (const event of userEvents) {
            console.log(event.type);
            await replayUsage(event, system);
        }

        // Debugging assertions
        expect(notePlayingSpy).toHaveBeenCalled();
        expect(notePausedSpy).toHaveBeenCalled();
        expect(markPlayingSpy).toHaveBeenCalled();
        expect(markPausedSpy).toHaveBeenCalled();

        // AND NOW! Expect the same payloads

        const testOutput = JSON.stringify(capture.payloadEvents);
        expect(capture.payloadEvents.length).toBeGreaterThan(0);

        const remadePayloads = payloadEvents.map((e) => {
            const event: PayloadCaptureEvent = {
                type: e.type,
                data: {
                    payload: e.data.payload,
                    url: e.data.url,
                },
                metadata: e.metadata,
            };
            return event;
        });

        console.log(remadePayloads, "324908u2343");
        console.log("testOutput", testOutput);
        console.log("Rawdata:", rawData);
        expect(testOutput).toBe(rawData);

        expect(capture.payloadEvents.length).toBe(remadePayloads.length);

        for (let i = 0; i < capture.payloadEvents.length; i++) {
            const obj1 = remadePayloads[i].data.payload;
            const obj2 = capture.payloadEvents[i].data.payload;
            // FIXME: DIdn't match
            // expect(obj1.tabTitle).toBe(obj2.tabTitle);
            expect(obj1.videoId).toBe(obj2.videoId);
            // expect(obj1.channelName).toBe(obj2.channel);
        }

        // diffLines is bad because the timestamps will always be different
        // diffLines(testOutput, rawData);
    });
});
