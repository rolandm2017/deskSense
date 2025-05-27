import { describe, expect, test } from "vitest";

import { InputCaptureManager } from "../../src/inputLogger/inputCaptureManager";

describe("Input capture", () => {
    //
    test("Session is automatically started on execution", () => {
        const manager = new InputCaptureManager({ enabled: true });
        const now = new Date();

        manager.logger.captureIfEnabled({
            type: "TEST_CAPTURE",
            data: { tabId: 2, url: "foo" },
            metadata: {
                source: "inputCapture.test",
                method: "user_input",
                location: "inputCapture.test",
                timestamp: new Date().toISOString(),
            },
        });

        expect(manager.logger.events.length).toBe(1);

        expect(manager.session.startTime.getTime()).toBe(now.getTime());
    });
    test("Gathers events as they happen", () => {
        const manager = new InputCaptureManager({ enabled: true });

        manager.logger.captureIfEnabled({
            type: "TEST_CAPTURE",
            data: { tabId: 2, url: "foo" },
            metadata: {
                source: "inputCapture.test",
                method: "user_input",
                location: "inputCapture.test",
                timestamp: new Date().toISOString(),
            },
        });
        manager.logger.captureIfEnabled({
            type: "TEST_CAPTURE",
            data: { tabId: 3, url: "bar" },
            metadata: {
                source: "inputCapture.test",
                method: "user_input",
                location: "inputCapture.test",
                timestamp: new Date().toISOString(),
            },
        });
        manager.logger.captureIfEnabled({
            type: "TEST_CAPTURE",
            data: { tabId: 4, url: "baz" },
            metadata: {
                source: "inputCapture.test",
                method: "user_input",
                location: "inputCapture.test",
                timestamp: new Date().toISOString(),
            },
        });

        expect(manager.logger.events.length).toBe(3);
    });
    test("Creates a downloadable log of events", () => {
        //
    });
    test("Session concludes after the allotted time", () => {
        // Run for 5 sec
    });
});
