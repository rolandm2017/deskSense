import { RECORDING_INPUT } from "../config";

interface UserAction {
    playerStateChange?: string;
}

interface UserActivity {
    time: Date;
    action: UserAction;
}

interface CaptureEvent {
    type: string;
    data: object;

    metadata: {
        source: string;
        method: string;
        location: string;
        timestamp: number;
    };
}

export class SystemInputLogger {
    // "A canonical semantic event is a clean, standardized representation of
    // what the user is trying to do, regardless of the technical messiness underneath"
    // Capture video play, pause
    // Capture URL, raw
    // Capture media title, raw

    events: CaptureEvent[];

    constructor() {
        this.events = [];
    }

    setupDetectorOnPage() {
        // runs once when the page loads
        //
    }

    captureIfEnabled(event: CaptureEvent) {
        console.log(event);
        console.log(
            "Pushing event data: ",
            event.data,
            RECORDING_INPUT.enabled
        );
        if (RECORDING_INPUT.enabled) {
            this.events.push(event);
        }
    }

    pushNewActivityToStorage(activity: string) {
        chrome.storage.local.get(["userActivityCapture"], function (result) {
            // Get current array or initialize empty array if it doesn't exist
            const currentActivity = result.userActivity || [];

            // Push the new item to the array
            currentActivity.push(activity);

            // Save the updated array back to storage
            chrome.storage.local.set(
                { userActivity: currentActivity },
                function () {
                    console.log("Array updated successfully");
                }
            );
        });
    }

    writeLogsToJson() {
        chrome.storage.local.get("userActivityCapture", (res) => {
            const blob = new Blob([JSON.stringify(res.writeLog, null, 2)], {
                type: "application/json",
            });
            const dateForTag = new Date();
            const dateString = dateForTag.toDateString();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `user-activity-capture-${dateString}.json`;
            a.click();
        });
    }
}

export const systemInputCapture = new SystemInputLogger();
