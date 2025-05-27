import chalk from "chalk";

import { PlatformType } from "../types/general.types";
import { CaptureEvent } from "./systemInputLogger";

console.log();
console.log(chalk.magenta("[Netflix]"), "⏸️  pause");

class LoggerStorageWriter {
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
}

export class PlatformLogger {
    platform: PlatformType;
    insert: string;
    chalkColor: Function;

    storageWriter: LoggerStorageWriter;

    constructor(platform: PlatformType) {
        this.platform = platform;
        this.storageWriter = new LoggerStorageWriter();

        if (platform === "YouTube") {
            this.chalkColor = chalk.red;
            this.insert = "[YouTube]";
        } else {
            this.chalkColor = chalk.magenta;
            this.insert = "[Netflix]";
        }
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

    logEventWithPayload(caller: string, url: string, payload: object) {
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
        this.storageWriter.storeEvent(event);
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

export function endpointLoggingDownload() {
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

export function clearEndpointLoggingStorage() {
    chrome.storage.local.set({ endpointActivity: [] }, function () {
        console.log("Everything deleted in endpointActivity");
    });
}
