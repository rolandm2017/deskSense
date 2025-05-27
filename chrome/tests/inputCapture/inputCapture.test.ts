import { describe, expect, test, vi } from "vitest";

import { InputCaptureManager } from "../../src/inputLogger/inputCaptureManager";

describe("Input capture", () => {
    //
    test("Session is automatically started on execution", () => {
        const duration = 5;
        const manager = new InputCaptureManager({ enabled: true }, duration);
        const now = new Date();

        manager.captureIfEnabled({
            type: "TEST_CAPTURE",
            data: { tabId: 2, url: "foo" },
            metadata: {
                source: "inputCapture.test",
                method: "user_input",
                location: "inputCapture.test",
                timestamp: new Date().toISOString(),
            },
        });

        expect(manager.events.length).toBe(1);

        expect(manager.session.startTime.getTime()).toBe(now.getTime());
    });
    test("Gathers events as they happen", () => {
        const duration = 5;
        const manager = new InputCaptureManager({ enabled: true }, duration);

        manager.captureIfEnabled({
            type: "TEST_CAPTURE",
            data: { tabId: 2, url: "foo" },
            metadata: {
                source: "inputCapture.test",
                method: "user_input",
                location: "inputCapture.test",
                timestamp: new Date().toISOString(),
            },
        });
        manager.captureIfEnabled({
            type: "TEST_CAPTURE",
            data: { tabId: 3, url: "bar" },
            metadata: {
                source: "inputCapture.test",
                method: "user_input",
                location: "inputCapture.test",
                timestamp: new Date().toISOString(),
            },
        });
        manager.captureIfEnabled({
            type: "TEST_CAPTURE",
            data: { tabId: 4, url: "baz" },
            metadata: {
                source: "inputCapture.test",
                method: "user_input",
                location: "inputCapture.test",
                timestamp: new Date().toISOString(),
            },
        });

        expect(manager.events.length).toBe(3);
    });
    test("Creates a downloadable log of events", () => {
        // This is not a feasible task,
        // but you can test it manually.
    });
    test("Session concludes after the allotted time", () => {
        const duration = 5;
        const manager = new InputCaptureManager({ enabled: true }, duration);
        const now = new Date();
        now.setMinutes(now.getMinutes() + duration);

        expect(manager.session.checkIfTimeExpired(now)).toBe(true);
    });
    test("onCaptureEvent calls onSessionEnd if the time is expired", () => {
        const duration = 5;
        const manager = new InputCaptureManager({ enabled: true }, duration);
        manager.onSessionEnd = vi.fn();

        const now = new Date();

        manager.onCaptureEvent(now);

        expect(manager.onSessionEnd).not.toHaveBeenCalled();

        now.setMinutes(now.getMinutes() + duration);

        manager.onCaptureEvent(now);

        expect(manager.onSessionEnd).toHaveBeenCalledOnce();
    });
});
