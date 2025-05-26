export const RECORDING_INPUT = { enabled: false };

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
        timestamp: string;
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
        if (RECORDING_INPUT.enabled) {
            console.log(event);
            console.log(
                "Pushing event data: ",
                event.data,
                RECORDING_INPUT.enabled
            );
            this.events.push(event);
            if (this.events.length % 5 == 0) {
                this.pushNewActivityToStorage(this.events);
            }
        }
    }

    pushNewActivityToStorage(activities: CaptureEvent[]) {
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

    writeLogsToJson() {
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

    clearStorage() {
        chrome.storage.local.set({ userActivityCapture: [] }, function () {
            console.log("userActivityCapture reset successfully");
        });
    }
}

export const systemInputCapture = new SystemInputLogger();
