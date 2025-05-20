import chalk from "chalk";

import { PlatformType } from "./types/general.types";

console.log();
console.log(chalk.magenta("[Netflix]"), "⏸️  pause");

class LoggerStorageWriter {
    savePayload(eventType: string, serverUrl: string, payload: object) {
        // gather metadata
        const metadata = {
            source: eventType,
            method: "POST",
            location: "api.ts",
            timestamp: new Date().toISOString(),
        };
        // TODO: log to json file
        chrome.storage.local.get(["endpointActivity"], function (result) {
            // Get current array or initialize empty array if it doesn't exist
            const currentActivity = result.endpointActivity || [];

            console.log("Writing payload with metadata", metadata);
            // Push the new item to the array
            currentActivity.push({ eventType, serverUrl, payload, metadata });

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
        console.log(tabTitle, "59ru");
        console.log(
            this.chalkColor(this.insert),
            "[info] On page: " + tabTitle
        );
    }

    logPlayEvent(mediaTitle?: string) {
        console.log(mediaTitle, "66ru");

        const identifier = mediaTitle ? ":: " + mediaTitle : "";
        console.log(this.chalkColor(this.insert), "▶️  play " + identifier);
    }

    logPauseEvent(mediaTitle?: string) {
        console.log(mediaTitle, "71ru");
        const identifier = mediaTitle ? ":: " + mediaTitle : "";

        console.log(this.chalkColor(this.insert), "⏸️  pause " + identifier);
    }

    logPayloadToStorage(eventType: string, serverUrl: string, payload: object) {
        // TODO: log to json file
        this.storageWriter.savePayload(eventType, serverUrl, payload);
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

    logPayloadToStorage(eventType: string, serverUrl: string, payload: object) {
        // TODO: log to json file
        // Consider it turned off if it's commented out
        // this.storageWriter.savePayload(eventType, serverUrl, payload);
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
