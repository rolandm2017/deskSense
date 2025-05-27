export const RECORDING_INPUT = { enabled: false };
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
export class SystemInputLogger {
    // "A canonical semantic event is a clean, standardized representation of
    // what the user is trying to do, regardless of the technical messiness underneath"
    // Capture video play, pause
    // Capture URL, raw
    // Capture media title, raw

    recording: { enabled: boolean };
    events: CaptureEvent[];

    private onCaptureCallback: (event: CaptureEvent) => void;

    constructor(
        isRecording: { enabled: boolean },
        onCaptureCallback: (event: CaptureEvent) => void
    ) {
        this.events = [];
        this.recording = isRecording;
        this.onCaptureCallback = onCaptureCallback;
    }

    captureIfEnabled(event: CaptureEvent) {
        if (this.recording.enabled) {
            console.log(event);
            console.log(
                "Pushing event data: ",
                event.data,
                this.recording.enabled
            );
            this.events.push(event);
            this.onCaptureCallback(event);
        }
    }
}
