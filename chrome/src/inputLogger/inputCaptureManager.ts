import { SystemInputLogger } from "./systemInputLogger";

import {
    endpointLoggingDownload,
    LoggerStorageWriter,
} from "./endpointLogging";

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
class InputCaptureSession {
    runTime: number;
    startTime: Date;
    constructor() {
        const RUN_TIME = 5;
        this.runTime = RUN_TIME * 1000; // ms
        this.startTime = new Date();
    }

    start() {}

    checkIfTimeExpired() {
        const currentTime = new Date();
        const expired =
            currentTime.getTime() - this.startTime.getTime() >= this.runTime;
        return expired;
    }

    end() {}
}

export class InputCaptureManager {
    recording: { enabled: boolean };
    session: InputCaptureSession;
    logger: SystemInputLogger;
    storage: LoggerStorageWriter | undefined;
    events: CaptureEvent[];

    constructor(
        isRecording: { enabled: boolean },
        storageWriter?: LoggerStorageWriter
    ) {
        this.recording = isRecording;

        this.events = [];
        this.session = new InputCaptureSession();
        this.logger = new SystemInputLogger(
            isRecording,
            (event: CaptureEvent) => {
                this.onCaptureEvent(event);
            }
        );

        this.storage = storageWriter;
    }

    captureIfEnabled(event: CaptureEvent) {
        if (this.recording.enabled) {
            console.log(
                "Pushing event data: ",
                event.data,
                this.recording.enabled
            );
            this.events.push(event);
            this.onCaptureEvent(event);
        }
    }

    onCaptureEvent(event: CaptureEvent) {
        this.session.checkIfTimeExpired();
        if (this.storage) {
            this.storage.pushUserActivityToStorage(this.events);
        }
    }

    endCapture() {}

    startCaptureSession() {
        // TODO: Reach out into CaptureLogger switch and activate it
        this.recording.enabled = true;
        this.session.start();
    }

    onSessionEnd() {
        const now = new Date();

        this.recording.enabled = false;
        this.session.end();
        endpointLoggingDownload();
        // Reset captureSessionStartTime
        // TODO: Download the logs as json
        console.log("Capture session ended");
    }

    // Reset everything
    reset() {
        // this.stopPolling();
        this.recording.enabled = false;
    }
}
