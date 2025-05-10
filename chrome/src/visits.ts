// visits.ts
import { pollingInterval } from "./channelExtractor";

// A Visit: As in, A PageVisit
// A Viewing: A window of time spent actively viewing the video.
// A Segment: A bundle of timestamps from your viewing. A viewing can have multiple segments.

/*
 * Server assumes that if Extension didn't send a "video ended" payload
 * before a tab change ...
 */

function getTimeSpentWatching() {
    return 5;
}

class VisitPayloadTimer {
    // a timer that tracks when to dispatch payload. KISS. Minimal.k
    dispatchTime: Date;

    constructor(dispatchTime: Date) {
        this.dispatchTime = dispatchTime;
    }

    timerHasElapsed(currentTime: Date) {
        const hoursElapsed =
            currentTime.getHours() >= this.dispatchTime.getHours();
        if (hoursElapsed) {
            // if the hours has elapsed, the rest is irrelevant
            return true;
        }
        const minutesElapsed =
            currentTime.getMinutes() >= this.dispatchTime.getMinutes();
        if (minutesElapsed) {
            // if the minutes has elapsed, the seconds are irrelevant
            return true;
        }
        const secondsElapsed =
            currentTime.getSeconds() >= this.dispatchTime.getSeconds();
        if (secondsElapsed) {
            return true;
        }
        return false;
    }
}

class VisitTracker {
    /*
     * Class is a container enabling cross-file visit management.
     */
    current: YouTubeVisit | NetflixVisit | undefined;
    timer: VisitPayloadTimer;

    constructor() {
        this.current = undefined;
        const v = new Date();
        const timerDuration = getTimeSpentWatching();
        const temp = new Date();
        this.timer = new VisitPayloadTimer(temp);
    }

    setCurrent(current: YouTubeVisit | NetflixVisit) {
        if (this.current) {
            if (this.current instanceof YouTubeVisit) {
                // report old Visit
                console.log("[debug] Reporting YouTube Visit");
                // api.reportYouTube("TODO", "TODO");
            } else {
                console.log("[debug] Reporting Netflix Visit");
                // api.reportNetflix("TODO", "TODO");
            }
        }
        this.current = current;
    }

    timerElapsed() {
        //
        this.timer;
        return true;
    }

    endVisit() {
        // used to report the final value on window close
        if (this.current) {
            this.current.conclude();
        }
    }
}

export const visitTracker = new VisitTracker();

class Segment {
    // A segment of time in a visit
    start: number;
    end: number;
    timestamps: number[];

    constructor(start: number, end: number) {
        this.start = start;
        this.end = end;
        this.timestamps = [];
    }

    addTimestamp(timestamp: number) {
        this.timestamps.push(timestamp);
        this.end = timestamp;
    }

    getDuration() {
        return this.end - this.start;
    }

    isFull() {
        return true;
    }
}

class VideoContentVisit {
    //
    videoId: string;
    tabTitle: string;
    timestamps: number[];
    playerState: "playing" | "paused";

    maxTimestampCount: number = 40;

    // probably want to send a payload every 3 minutes or so, max.

    constructor(videoId: string, tabTitle: string) {
        this.videoId = videoId;
        this.tabTitle = tabTitle;
        this.timestamps = [];
        this.playerState = "paused";
    }

    sendInitialInfoToServer() {
        // delivers initial info
    }

    addTimestamp(timestamp: number) {
        this.timestamps.push(timestamp);
    }

    sufficientDurationForReport() {
        // if the visit lasted 60 sec, report it and start fresh.
    }

    // Can tell also *how long* player was paused for.

    isStillPlaying() {
        const previous = this.timestamps.at(-2);
        const current = this.timestamps.at(-1);
        if (previous && current) {
            const gap = previous - current;
            const stillPlaying = gap === pollingInterval;
            if (stillPlaying) {
                // still playing
                this.playerState = "playing";
            } else {
                // paused
                this.playerState = "paused";
            }
        }
    }

    finishIfFull() {
        const full = true;
    }

    conclude() {
        // delivers final data
        // api.sendPayload
    }
}

export class NetflixVisit extends VideoContentVisit {
    // TODO
    contentTitle: string;

    constructor(videoId: string, tabTitle: string, contentTitle: string) {
        super(videoId, tabTitle);
        this.contentTitle = contentTitle;
        // timestamps arr in superclass
    }
}

export class YouTubeVisit extends VideoContentVisit {
    channelName: string;

    constructor(videoId: string, tabTitle: string, channelName: string) {
        super(videoId, tabTitle);
        this.channelName = channelName;
        // timestamps arr in superclass
    }
}
