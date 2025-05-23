// videoCommon/visits.ts

import { initializedServerApi, ServerApi } from "../api";
import { MissingMediaError } from "../errors";
import {
    INetflixViewing,
    IStatelessNetflixViewing,
    IYouTubeViewing,
    NetflixPayload,
    YouTubePayload,
} from "../interface/interfaces";

import { PlatformLogger } from "../endpointLogging";

// A Visit: As in, A PageVisit
// A Viewing: A window of time spent actively viewing the video.

/*
 * Server assumes that if Extension didn't send a "video ended" payload
 * before a tab change ...
 */

export class ViewingTracker {
    /*
     * Class is a container enabling cross-file Viewing management.
     */
    currentMedia: YouTubeViewing | NetflixViewing | undefined;
    mostRecentReport: YouTubeViewing | undefined;
    autoplayWaiting: boolean;
    youTubeApiLogger: PlatformLogger;
    netflixApiLogger: PlatformLogger;
    api: ServerApi;

    partialNetflixDescriptor: string | undefined;

    constructor(api: ServerApi) {
        this.api = api;
        this.mostRecentReport = undefined;
        this.autoplayWaiting = false;
        this.currentMedia = undefined;
        this.partialNetflixDescriptor = undefined;
        this.youTubeApiLogger = new PlatformLogger("YouTube");
        this.netflixApiLogger = new PlatformLogger("Netflix");
        // TODO: JUST ASSUME it's going to work with Play/Pause only,
        // until you figure out otherwise.
    }

    setCurrent(current: YouTubeViewing | NetflixViewing) {
        this.currentMedia = current;
    }

    markAutoplayEventWaiting() {
        // Don't send the play event right away like usual.
        // Instead, note that one is waiting to be delivered,
        // and bundle it in with the Watch Page report.
        this.autoplayWaiting = true;
    }

    reportYouTubeWatchPage() {
        // FIXME: It's the case that, when you refresh, the
        // NewPageLoad event (this thing) goes off, BUT the video is playing!
        // And there is no notification of it BEING playing! No indication.

        if (this.currentMedia instanceof YouTubeViewing) {
            this.mostRecentReport = this.currentMedia;
            // this.youTubeApiLogger.logLandOnPage(this.currentMedia.mediaTitle);
            this.api.youtube.reportYouTubeWatchPage(
                this.currentMedia.mediaTitle,
                this.currentMedia.videoId,
                this.currentMedia.channelName,
                this.autoplayWaiting ? "playing" : "paused"
            );
            this.autoplayWaiting = false;
            return;
        }
        throw new Error("Incorrect media type for YouTube reporting");
    }

    reportNetflixWatchPage(fullUrl: string, urlId: string) {
        // Netflix pages show their eventual url in an instant, but the program
        // must wait for the user to tell the program which media it is.
        // Hence a "reportWatchPage" from Netflix can only reliably contain
        // the videoId from the URL.
        const partiallyDescribedMedia: string = urlId;
        this.partialNetflixDescriptor = partiallyDescribedMedia;
        this.api.netflix.reportPartialNetflixWatchPage(
            fullUrl,
            partiallyDescribedMedia,
            this.autoplayWaiting ? "playing" : "paused"
        );
        this.autoplayWaiting = false;
    }

    reportFilledNetflixWatch(netflixMedia: NetflixViewing) {
        this.api.netflix.reportFilledNetflixWatchPage(netflixMedia);
    }

    markPlaying() {
        if (!this.currentMedia) {
            throw new MissingMediaError();
        }
        this.currentMedia.playerState = "playing";
        if (this.currentMedia instanceof YouTubeViewing) {
            console.log("Media is YouTubeViewing");
            // this.youTubeApiLogger.logPlayEvent();
            const asYouTubePayload = this.currentMedia.convertToPayload();
            console.log("sending play event");
            this.api.youtube.sendPlayEvent(asYouTubePayload);
        } else {
            console.log("Media is NetflixViewing");
            // this.netflixApiLogger.logPlayEvent();
            const asNetflixPayload = this.currentMedia.convertToPayload();
            console.log("sending play event");
            this.api.netflix.sendPlayEvent(asNetflixPayload);
        }
    }

    silentlyMarkPlaying() {
        // silentlyMarkPlaying does not alert the server of the play event,
        // because the server heard about the play event in the page payload.
        if (!this.currentMedia) {
            throw new MissingMediaError();
        }
        this.currentMedia.playerState = "playing";
    }

    markPaused() {
        if (!this.currentMedia) {
            throw new MissingMediaError();
        }
        this.currentMedia.playerState = "paused";

        if (this.currentMedia instanceof YouTubeViewing) {
            // this.youTubeApiLogger.logPauseEvent();
            const asYouTubePayload = this.currentMedia.convertToPayload();
            console.log("sending pause event");
            this.api.youtube.sendPauseEvent(asYouTubePayload);
        } else {
            // this.netflixApiLogger.logPauseEvent();
            const asNetflixPayload = this.currentMedia.convertToPayload();
            console.log("sending pause event");
            this.api.netflix.sendPauseEvent(asNetflixPayload);
        }
    }

    endViewing() {
        // TODO: handle the user closing the tab
        // used to report the final value on window close
        this.mostRecentReport = undefined;
        if (this.currentMedia) {
            // conclude. something like:
            // this.api.platform.sendClosePage() // does wrapup
            // this.currentMedia.conclude();
        }
    }
}

export const viewingTracker = new ViewingTracker(initializedServerApi);

export class YouTubeViewing implements IYouTubeViewing {
    videoId: string;
    url: string;
    mediaTitle: string;
    timestamps: number[];
    playerState: "playing" | "paused";
    // unique to this class
    channelName: string;

    // Can tell also *how long* player was paused for.

    constructor(
        videoId: string,
        url: string,
        tabTitle: string,
        channelName: string
    ) {
        this.videoId = videoId;
        this.url = url;
        this.mediaTitle = tabTitle;
        this.channelName = channelName;
        this.timestamps = [];
        this.playerState = "paused";
    }

    convertToPayload(): YouTubePayload {
        return {
            url: this.url,
            videoId: this.videoId,
            tabTitle: this.mediaTitle,
            channelName: this.channelName,
        };
    }
}

export class NetflixViewingSansState implements IStatelessNetflixViewing {
    videoId: string;
    mediaTitle: string;
    url: string;
    constructor(videoId: string, showName: string, url: string) {
        // the Url ID becomes the VideoID.
        this.videoId = videoId;
        // the showName becomes the mediaTitle.
        this.mediaTitle = showName;
        this.url = url;
    }
}

export class NetflixViewing
    extends NetflixViewingSansState
    implements INetflixViewing
{
    videoId: string;
    mediaTitle: string;
    playerState: "playing" | "paused";
    // TODO
    constructor(
        videoId: string,
        showName: string,
        url: string,
        playerState: "playing" | "paused"
    ) {
        super(videoId, showName, url);
        // the Url ID becomes the VideoID.
        this.videoId = videoId;
        // the showName becomes the mediaTitle.
        this.mediaTitle = showName;
        this.playerState = playerState;
    }

    convertToPayload(): NetflixPayload {
        return {
            showName: this.mediaTitle,
            videoId: this.videoId,
        };
    }
}
