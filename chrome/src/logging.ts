import chalk from "chalk";

import { PlatformType } from "./types/general.types";

console.log();
console.log(chalk.magenta("[Netflix]"), "⏸️  pause");

export class PlatformLogger {
    platform: PlatformType;
    insert: string;
    chalkColor: Function;

    constructor(platform: PlatformType) {
        this.platform = platform;

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
        console.log(
            this.chalkColor(this.insert),
            "▶️  play " + mediaTitle ? ":: " + mediaTitle : ""
        );
    }

    logPauseEvent(mediaTitle?: string) {
        console.log(
            this.chalkColor(this.insert),
            "⏸️  pause " + mediaTitle ? ":: " + mediaTitle : ""
        );
    }

    logPayloadToStorage(eventType: string, serverUrl: string, payload: object) {
        // TODO: log to json file
        chrome.storage.local.get(["endpointActivity"], function (result) {
            // Get current array or initialize empty array if it doesn't exist
            const currentActivity = result.endpointActivity || [];

            // Push the new item to the array
            currentActivity.push({ eventType, serverUrl, payload });

            // Save the updated array back to storage
            chrome.storage.local.set(
                { endpointActivity: currentActivity },
                function () {
                    console.log("Array updated successfully");
                }
            );
        });
    }

    writeLogsToJson() {
        // look at endpointLoggingDownload()
    }
}

export class DomainLogger {
    constructor() {}

    logTabSwitch() {
        console.log("🌐 [API] 🌍  Switched to domain: youtube.com");
    }

    logPayload(eventType: string, serverUrl: string, payload: object) {
        // TODO: log to json file
    }
}

export function endpointLoggingDownload() {
    chrome.storage.local.get("endpointActivity", (res) => {
        const blob = new Blob([JSON.stringify(res.writeLog, null, 2)], {
            type: "application/json",
        });
        const dateString = new Date().toDateString();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `endpoint-activity-${dateString}.json`;
        a.click();
    });
}
