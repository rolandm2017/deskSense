import { CaptureEvent, SystemInputLogger } from "./systemInputLogger";

const RECORDING_INPUT = { enabled: false };
class InputCaptureSession {
    runTime: number;
    startTime: Date;
    constructor() {
        // foo
        this.runTime = 5 * 1000; // ms
        this.startTime = new Date();
    }

    start() {
        // foo
    }

    checkIfTimeExpired() {
        const currentTime = new Date();
        const expired =
            currentTime.getTime() - this.startTime.getTime() >= this.runTime;
        return expired;
    }

    end() {
        // foo
    }
}

export class InputCaptureManager {
    runPolling: boolean;
    captureSessionStartTime: Date | undefined;
    session: InputCaptureSession;
    logger: SystemInputLogger;
    sessionEndCheckIntervalId: number | null;

    constructor() {
        this.runPolling = false;
        this.captureSessionStartTime = undefined;
        this.session = new InputCaptureSession();
        this.logger = new SystemInputLogger((event: CaptureEvent) => {
            this.onCaptureEvent(event);
        });
        this.sessionEndCheckIntervalId = null;
    }

    onCaptureEvent(event: CaptureEvent) {
        this.session.checkIfTimeExpired();
    }

    endCapture() {}

    startCaptureSession() {
        // TODO: Reach out into CaptureLogger switch and activate it
        RECORDING_INPUT.enabled = true;
        this.session.start();
    }

    onSessionEnd() {
        const now = new Date();
        if (this.captureSessionStartTime === undefined) {
            return;
        }

        RECORDING_INPUT.enabled = false;
        this.session.end();
        this.logger.writeLogsToJson();
        // Reset captureSessionStartTime
        this.captureSessionStartTime = undefined;
        // TODO: Download the logs as json
        console.log("Capture session ended");
    }

    // Reset everything
    reset() {
        // this.stopPolling();
        this.captureSessionStartTime = undefined;
        RECORDING_INPUT.enabled = false;
    }
}
