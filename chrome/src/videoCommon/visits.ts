// visits.ts

import { ServerApi } from "../api";
import { WatchEntry } from "../interface/interfaces";
import { PlatformLogger } from "../logging";

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

export class ViewingTracker {
    /*
     * Class is a container enabling cross-file Viewing management.
     */
    currentMedia: YouTubeViewing | NetflixViewing | undefined;
    youTubeApiLogger: PlatformLogger;
    netflixApiLogger: PlatformLogger;
    api: ServerApi;

    partialNetflixDescriptor: string | undefined;
    // timer: ViewingPayloadTimer;

    constructor(api: ServerApi) {
        this.currentMedia = undefined;
        this.partialNetflixDescriptor = undefined;
        this.api = api;
        this.youTubeApiLogger = new PlatformLogger("YouTube");
        this.netflixApiLogger = new PlatformLogger("Netflix");
        // TODO: JUST ASSUME it's going to work with Play/Pause only, until
        // UNTIL you figure out otherwise.
        // const timerDuration = getTimeSpentWatching();
        // const temp = new Date();
        // this.timer = new ViewingPayloadTimer(temp);
    }

    setCurrent(current: YouTubeViewing | NetflixViewing) {
        console.log("In setCurrent", current);
        this.currentMedia = current;
        if (current instanceof YouTubeViewing) {
            console.log("Would report youtube here");
            this.youTubeApiLogger.logLandOnPage();
            // api.reportYouTubePage();
        } else {
            console.log("Would report netflix here");
            this.netflixApiLogger.logLandOnPage();
        }
    }

    reportNetflixWatchPage(watchPageId: string) {
        // Netflix pages show their eventual url in an instant, but the program
        // must wait for the user to tell the program which media it is.
        // Hence a "reportWatchPage" from Netflix can only reliably contain
        // the videoId from the URL.
        const partiallyDescribedMedia: string = watchPageId;
        this.partialNetflixDescriptor = partiallyDescribedMedia;
        this.api;
    }

    reportYouTubeWatchPage() {
        if (this.currentMedia instanceof YouTubeViewing) {
            this.youTubeApiLogger.logLandOnPage();
            this.api.youtube.reportYouTubePage(
                this.currentMedia.mediaTitle,
                this.currentMedia.channelName
            );
            return;
        }
        throw new Error("Incorrect media type for YouTube reporting");
    }

    markPlaying() {
        if (this.currentMedia instanceof YouTubeViewing) {
            this.youTubeApiLogger.logPlayEvent();
            this.api.youtube.sendPlayEvent(this.currentMedia);
        } else {
            this.netflixApiLogger.logPlayEvent();
            this.api.netflix.sendPlayEvent(this.currentMedia);
        }
    }

    markPaused() {
        if (this.currentMedia instanceof YouTubeViewing) {
            this.youTubeApiLogger.logPauseEvent();
            this.api.youtube.sendPauseEvent(this.currentMedia);
        } else {
            this.netflixApiLogger.logPauseEvent();
            this.api.netflix.sendPauseEvent(this.currentMedia);
        }
    }

    endViewing() {
        // used to report the final value on window close
        if (this.currentMedia) {
            // conclude. something like:
            // this.api.platform.sendClosePage() // does wrapup
            // this.currentMedia.conclude();
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
}

class VideoContentViewing {
    // Note that these property names must work for Netflix & YouTube both.
    // Probably want to send a payload every 3 minutes or so, max.
}

export class YouTubeViewing {
    videoId: string;
    mediaTitle: string;
    timestamps: number[];
    playerState: "playing" | "paused";
    // unique to this class
    channelName: string;

    // Can tell also *how long* player was paused for.

    // TODO: If pause lasts only five sec, ignore that it was paused
    //      -> do not send payload
    //      -> do not even stop tracking time

    constructor(videoId: string, tabTitle: string, channelName: string) {
        this.videoId = videoId;
        this.mediaTitle = tabTitle;
        this.channelName = channelName;
        this.timestamps = [];
        this.playerState = "paused";
    }
}

export class NetflixViewing {
    videoId: string;
    mediaTitle: string;
    timestamps: number[];
    playerState: "playing" | "paused";
    // TODO
    constructor(watchEntry: WatchEntry) {
        // the Url ID becomes the VideoID.
        this.videoId = watchEntry.urlId;
        // the showName becomes the mediaTitle.
        this.mediaTitle = watchEntry.showName;
        this.timestamps = [];
        this.playerState = "paused";
    }
}
