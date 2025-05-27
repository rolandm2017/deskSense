import { SystemInputLogger } from "./systemInputLogger";

const RECORDING_INPUT = { enabled: false };
class InputCaptureSession {
    constructor() {
        // foo
    }

    start() {
        // foo
    }

    end() {
        // foo
    }
}

export class InputCaptureManager {
    runPolling: boolean;
    captureSessionStartTime: Date | undefined;
    inputCaptureSession: InputCaptureSession;
    systemInputLogger: SystemInputLogger;
    sessionEndCheckIntervalId: number | null;

    constructor(systemInputLogger: SystemInputLogger) {
        this.runPolling = false;
        this.captureSessionStartTime = undefined;
        this.inputCaptureSession = new InputCaptureSession();
        this.systemInputLogger = systemInputLogger;
        this.sessionEndCheckIntervalId = null;

        // Bind methods to preserve 'this' context
        this.processTestStartTime = this.processTestStartTime.bind(this);
    }

    getTestStartTime() {
        //
    }

    processTestStartTime(response: Response) {
        this.startCaptureSession();

        // Start checking for session end
        this.startSessionEndChecking();
    }

    startCaptureSession() {
        // TODO: Reach out into CaptureLogger switch and activate it
        RECORDING_INPUT.enabled = true;
        this.inputCaptureSession.start();
    }

    // Start checking for session end
    startSessionEndChecking() {
        // Check every minute for session end
        this.sessionEndCheckIntervalId = window.setInterval(() => {
            this.checkForSessionEnd();
        }, 60000); // Check every minute

        console.log("Session end checking started");
    }

    checkForSessionEnd() {
        const now = new Date();
        if (this.captureSessionStartTime === undefined) {
            return;
        }

        // Fixed the hour comparison logic
        const oneHourSinceStart =
            now.getTime() - this.captureSessionStartTime.getTime() >= 3600000; // 1 hour in milliseconds

        if (oneHourSinceStart) {
            RECORDING_INPUT.enabled = false;
            this.inputCaptureSession.end();
            this.systemInputLogger.writeLogsToJson();
            // Reset captureSessionStartTime
            this.captureSessionStartTime = undefined;
            // Stop checking for session end
            this.stopSessionEndChecking();
            // TODO: Download the logs as json
            console.log("Capture session ended");
        }
    }

    // Stop checking for session end
    stopSessionEndChecking() {
        if (this.sessionEndCheckIntervalId !== null) {
            window.clearInterval(this.sessionEndCheckIntervalId);
            this.sessionEndCheckIntervalId = null;
        }
        console.log("Session end checking stopped");
    }

    // Reset everything
    reset() {
        // this.stopPolling();
        this.stopSessionEndChecking();
        this.captureSessionStartTime = undefined;
        RECORDING_INPUT.enabled = false;
    }
}
