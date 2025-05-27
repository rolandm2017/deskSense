import chalk from "chalk";

import { PlatformType } from "../types/general.types";
import {
    CaptureEvent,
    InputCaptureManager,
    InputCaptureSession,
} from "./inputCaptureManager";

console.log();
console.log(chalk.magenta("[Netflix]"), "⏸️  pause");

export class LoggerStorageWriter {
    storeEvent(event: CaptureEvent) {
        // gather metadata
        // TODO: log to json file
        chrome.storage.local.get(["endpointActivity"], function (result) {
            // Get current array or initialize empty array if it doesn't exist
            const currentActivity = result.endpointActivity || [];

            console.log("Writing payload with metadata", event.metadata);
            // Push the new item to the array
            currentActivity.push(event);

            // Save the updated array back to storage
            chrome.storage.local.set(
                { endpointActivity: currentActivity },
                function () {
                    console.log("Array updated successfully");
                }
            );
        });
    }

    pushUserActivityToStorage(activities: CaptureEvent[]) {
        console.log("Pushing new activity to storage");
        chrome.storage.local.get(["userActivityCapture"], function (result) {
            // Get current array or initialize empty array if it doesn't exist
            const currentActivity = result.userActivity || [];

            // Push the new item to the array
            // currentActivity.push(activity);

            // Save the updated array back to storage
            chrome.storage.local.set(
                { userActivityCapture: activities },
                function () {
                    console.log("Array updated successfully");
                }
            );
        });
    }

    writeUserActivityLogsToJson() {
        chrome.storage.local.get("userActivityCapture", (res) => {
            console.log(res, "RES for userActivityCapture");

            const jsonString = JSON.stringify(res.userActivityCapture, null, 2);
            const dataUrl =
                "data:application/json;charset=utf-8," +
                encodeURIComponent(jsonString);

            const dateString = new Date().toDateString();

            // Use chrome.downloads API instead of the anchor trick
            chrome.downloads.download({
                url: dataUrl,
                filename: `user-activity-capture-${dateString}.json`,
                saveAs: true,
            });
        });
    }

    clearUserActivityStorage() {
        chrome.storage.local.set({ userActivityCapture: [] }, function () {
            console.log("userActivityCapture reset successfully");
        });
    }
}

export class PlatformLogger {
    platform: PlatformType;
    insert: string;
    chalkColor: Function;

    session: InputCaptureSession;
    captureManager: InputCaptureManager;

    storageWriter: LoggerStorageWriter;

    constructor(platform: PlatformType, captureManager: InputCaptureManager) {
        this.platform = platform;
        this.captureManager = captureManager;
        this.session = captureManager.session;
        this.storageWriter = new LoggerStorageWriter();

        if (platform === "YouTube") {
            this.chalkColor = chalk.red;
            this.insert = "[YouTube]";
        } else {
            this.chalkColor = chalk.magenta;
            this.insert = "[Netflix]";
        }
    }

    logEventWithPayload(caller: string, url: string, payload: object) {
        const expired = this.session.checkIfTimeExpired(new Date());
        if (expired) {
            console.warn("Capture session expired");
            console.warn("Capture session expired");
            console.warn("Capture session expired");
            console.warn("Capture session expired");
            return;
        }
        const event: CaptureEvent = {
            type: caller,
            data: { payload, url },
            metadata: {
                source: "api.ts",
                method: caller,
                location: caller,
                timestamp: new Date().toISOString(),
            },
        };
        this.captureManager.payloadEvents.push(event);
        this.storageWriter.storeEvent(event);
    }

    logEventCount() {
        console.log("Event count: ", this.captureManager.payloadEvents.length);
    }

    logLandOnPage(tabTitle: string) {
        // TODO: Make Netflix magenta
        console.log(
            this.chalkColor(this.insert),
            "[info] On page: " + tabTitle
        );
    }

    logPlayEvent(mediaTitle?: string) {
        const identifier = mediaTitle ? ":: " + mediaTitle : "";
        console.log(this.chalkColor(this.insert), "▶️  play " + identifier);
    }

    logPauseEvent(mediaTitle?: string) {
        const identifier = mediaTitle ? ":: " + mediaTitle : "";

        console.log(this.chalkColor(this.insert), "⏸️  pause " + identifier);
    }

    writeLogsToJson() {
        // look at endpointLoggingDownload()
    }
}

export class DomainLogger {
    storageWriter: LoggerStorageWriter;

    constructor() {
        this.storageWriter = new LoggerStorageWriter();
    }

    logTabSwitch() {
        console.log("🌐 [API] 🌍  Switched to domain: youtube.com");
    }

    logEventWithPayload(caller: string, url: string, payload: object) {
        //
    }
}

function endpointLoggingDownload() {
    chrome.storage.local.get("endpointActivity", (res) => {
        // Create a data URL instead of using createObjectURL
        console.log(res, "endpointActivity RES");
        const jsonString = JSON.stringify(res.endpointActivity, null, 2);
        const dataUrl =
            "data:application/json;charset=utf-8," +
            encodeURIComponent(jsonString);

        const dateString = new Date().toDateString();

        // Use chrome.downloads API instead of the anchor trick
        chrome.downloads.download({
            url: dataUrl,
            filename: `endpoint-activity-${dateString}.json`,
            saveAs: true,
        });
    });
}

function clearEndpointLoggingStorage() {
    chrome.storage.local.set({ endpointActivity: [] }, function () {
        console.log("Everything deleted in endpointActivity");
    });
}
