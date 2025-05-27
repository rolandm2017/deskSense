import { LoggerStorageWriter } from "./endpointLogging";

export interface CaptureEvent {
    type: string;
    data: object;

    metadata: {
        source: string;
        method: string;
        location: string;
        timestamp: string;
    };
}
export class InputCaptureSession {
    runTime: number;
    startTime: Date;
    constructor(runTimeInMinutes: number) {
        this.runTime = runTimeInMinutes * 60 * 1000; // ms
        this.startTime = new Date();
    }

    checkIfTimeExpired(currentTime: Date) {
        const expired =
            currentTime.getTime() - this.startTime.getTime() >= this.runTime;
        return expired;
    }

    getRemainingTime(currentTime: Date) {
        const elapsed = currentTime.getTime() - this.startTime.getTime();
        const remaining = Math.max(0, this.runTime - elapsed); // Don't go negative

        const minutes = Math.floor(remaining / (60 * 1000));
        const seconds = Math.floor((remaining % (60 * 1000)) / 1000);

        return `${minutes.toString().padStart(2, "0")}:${seconds
            .toString()
            .padStart(2, "0")}`;
    }
}

export class InputCaptureManager {
    recording: { enabled: boolean };
    session: InputCaptureSession;
    storage: LoggerStorageWriter | undefined;
    events: CaptureEvent[];
    payloadEvents: CaptureEvent[];

    constructor(
        isRecording: { enabled: boolean },
        runtimeInMin: number,
        storageWriter?: LoggerStorageWriter
    ) {
        this.recording = isRecording;

        if (isRecording.enabled) {
            console.log("Running test for " + runtimeInMin + " minutes");
        }

        this.events = [];
        this.payloadEvents = [];
        this.session = new InputCaptureSession(runtimeInMin);

        this.storage = storageWriter;
    }

    captureIfEnabled(event: CaptureEvent) {
        console.log("capture if enabled", event.type);
        console.log("capture if enabled", event.type);
        console.log("capture if enabled", event.type);
        if (this.recording.enabled) {
            console.log(
                "Pushing event data: ",
                event.data,
                this.recording.enabled
            );
            this.events.push(event);
            this.onCaptureEvent(new Date());
        }
    }

    onCaptureEvent(now: Date) {
        if (this.storage) {
            this.storage.pushUserActivityToStorage(this.events);
        }
        const expired = this.session.checkIfTimeExpired(now);
        if (expired) {
            this.onSessionEnd();
        }
    }

    onSessionEnd() {
        this.recording.enabled = false;
        // Reset captureSessionStartTime
        // TODO: Download the logs as json
        console.log("Capture session ended");
        console.log("Capture session ended");
        console.log("Capture session ended");
        console.log("Capture session ended");
        console.log("Capture session ended");
        console.log("Capture session ended");
        console.log("Capture session ended");
        this.downloadUserEvents();
        this.downloadPayloadEvents();
    }

    downloadUserEvents() {
        const jsonString = JSON.stringify(this.events, null, 2);
        const dataUrl =
            "data:application/json;charset=utf-8," +
            encodeURIComponent(jsonString);

        const dateString = new Date().toDateString();

        // Use chrome.downloads API instead of the anchor trick
        chrome.downloads.download({
            url: dataUrl,
            filename: `user-input-activity-${dateString}.json`,
            saveAs: true,
        });
    }

    downloadPayloadEvents() {
        const jsonString = JSON.stringify(this.payloadEvents, null, 2);
        const dataUrl =
            "data:application/json;charset=utf-8," +
            encodeURIComponent(jsonString);

        const dateString = new Date().toDateString();

        // Use chrome.downloads API instead of the anchor trick
        chrome.downloads.download({
            url: dataUrl,
            filename: `payload-events-${dateString}.json`,
            saveAs: true,
        });
    }

    // Reset everything
    reset() {
        this.recording.enabled = false;
    }

    showRemainingTime() {
        console.log(this.session.getRemainingTime(new Date()));
    }
}
