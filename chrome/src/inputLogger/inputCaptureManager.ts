import { ServerApi } from "../api";
import { RECORDING_INPUT } from "../config";
import { SystemInputLogger } from "./systemInputLogger";

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
    api: ServerApi;
    runPolling: boolean;
    captureSessionStartTime: Date | undefined;
    inputCaptureSession: InputCaptureSession;
    systemInputLogger: SystemInputLogger;
    pollingIntervalId: number | null;
    sessionEndCheckIntervalId: number | null;

    constructor(systemInputLogger: SystemInputLogger, api: ServerApi) {
        this.api = api;
        this.runPolling = false;
        this.captureSessionStartTime = undefined;
        this.inputCaptureSession = new InputCaptureSession();
        this.systemInputLogger = systemInputLogger;
        this.pollingIntervalId = null;
        this.sessionEndCheckIntervalId = null;

        // Bind methods to preserve 'this' context
        this.processTestStartTime = this.processTestStartTime.bind(this);
    }

    // Start polling for capture session
    startPolling() {
        // Don't start if already polling
        if (this.pollingIntervalId !== null) return;

        this.runPolling = true;
        // Poll every second
        this.pollingIntervalId = window.setInterval(() => {
            this.getTestStartTime();
        }, 1000);

        console.log("Polling for capture session started");
    }

    // Stop polling for capture session
    stopPolling() {
        if (this.pollingIntervalId !== null) {
            window.clearInterval(this.pollingIntervalId);
            this.pollingIntervalId = null;
        }
        this.runPolling = false;
        console.log("Polling for capture session stopped");
    }

    getTestStartTime() {
        this.api.checkForCaptureSession(this.processTestStartTime);
    }

    processTestStartTime(response: Response) {
        response.json().then((result) => {
            if (result.captureSessionStartTime) {
                this.captureSessionStartTime = new Date(
                    result.captureSessionStartTime
                );
                console.log(
                    "Starting capture session at : ",
                    this.captureSessionStartTime
                );

                // Stop polling once we've found a session
                // this.stopPolling();

                // Start the capture session
                this.startCaptureSession();

                // Start checking for session end
                this.startSessionEndChecking();
            } else {
                console.log("Nothing yet");
            }
        });
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
