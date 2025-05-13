// visits.ts

import { api } from "./api";

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

class ViewingPayloadTimer {
    // a timer that tracks when to dispatch payload. KISS. Minimal.
    dispatchTime: Date;

    // TODO: Every two minutes send a KeepAlive signal: "Yep, still here"
    // If no KeepAlive signal, end session after five minutes.

    /*

    YouTube is a mixture of play/pause plus polling.

    */

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

class ViewingTracker {
    /*
     * Class is a container enabling cross-file Viewing management.
     */
    current: YouTubeViewing | NetflixViewing | undefined;
    timer: ViewingPayloadTimer;

    constructor() {
        this.current = undefined;
        const v = new Date();
        const timerDuration = getTimeSpentWatching();
        const temp = new Date();
        this.timer = new ViewingPayloadTimer(temp);
    }

    setCurrent(current: YouTubeViewing | NetflixViewing) {
        this.current = current;
    }

    timerElapsed() {
        //
        this.timer;
        return true;
    }

    endViewing() {
        // used to report the final value on window close
        if (this.current) {
            this.current.conclude();
        }
    }
}

export const viewingTracker = new ViewingTracker();

class Segment {
    // A segment of time in a Viewing
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

class VideoContentViewing {
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

    startTimeTracking() {
        throw new Error("Not yet implemented");
    }

    pauseTracking() {
        throw new Error("Not yet implemented");
    }

    sendInitialInfoToServer() {
        // delivers initial info
    }

    addTimestamp(timestamp: number) {
        this.timestamps.push(timestamp);
    }

    sufficientDurationForReport() {
        // if the Viewing lasted 60 sec, report it and start fresh.
    }

    // Can tell also *how long* player was paused for.

    // TODO: If pause lasts only five sec, ignore that it was paused
    //      -> do not send payload
    //      -> do not even stop tracking time

    isStillPlaying() {
        const previous = this.timestamps.at(-2);
        const current = this.timestamps.at(-1);
        if (previous && current) {
            const gap = previous - current;
            const stillPlaying = gap === 2000;
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

export class YouTubeViewing extends VideoContentViewing {
    channelName: string;

    constructor(videoId: string, tabTitle: string, channelName: string) {
        super(videoId, tabTitle);
        this.channelName = channelName;
        // timestamps arr in superclass
    }

    startTimeTracking() {
        api.youtube.sendPlayEvent(this);
    }

    pauseTracking() {
        api.youtube.sendPauseEvent(this);
    }
}

export class NetflixViewing extends VideoContentViewing {
    // TODO
    contentTitle: string;

    constructor(videoId: string, tabTitle: string, contentTitle: string) {
        super(videoId, tabTitle);
        this.contentTitle = contentTitle;
        // timestamps arr in superclass
    }

    startTimeTracking() {
        api.netflix.sendPlayEvent();
    }

    pauseTracking() {
        api.netflix.sendPauseEvent();
    }
}
