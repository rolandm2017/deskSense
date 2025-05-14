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

class SystemInputLogger {
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

    capture(event: CaptureEvent) {
        this.events.push(event);
    }

    pushNewActivityToStorage(activity: string) {
        chrome.storage.local.get(["userActivity"], function (result) {
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
        chrome.storage.local.get("writeLog", (res) => {
            const blob = new Blob([JSON.stringify(res.writeLog, null, 2)], {
                type: "application/json",
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "write-log.json";
            a.click();
        });
    }
}

export const systemInputCapture = new SystemInputLogger();
