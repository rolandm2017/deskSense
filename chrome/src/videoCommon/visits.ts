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
    youTubeApiLogger: PlatformLogger;
    netflixApiLogger: PlatformLogger;
    api: ServerApi;

    partialNetflixDescriptor: string | undefined;

    constructor(api: ServerApi) {
        this.currentMedia = undefined;
        this.partialNetflixDescriptor = undefined;
        this.api = api;
        this.youTubeApiLogger = new PlatformLogger("YouTube");
        this.netflixApiLogger = new PlatformLogger("Netflix");
        // TODO: JUST ASSUME it's going to work with Play/Pause only,
        // until you figure out otherwise.
    }

    setCurrent(current: YouTubeViewing | NetflixViewing) {
        this.currentMedia = current;
    }

    reportNetflixWatchPage(watchPageId: string) {
        // Netflix pages show their eventual url in an instant, but the program
        // must wait for the user to tell the program which media it is.
        // Hence a "reportWatchPage" from Netflix can only reliably contain
        // the videoId from the URL.
        const partiallyDescribedMedia: string = watchPageId;
        this.partialNetflixDescriptor = partiallyDescribedMedia;
        this.api.netflix.reportNetflixPage(partiallyDescribedMedia);
    }

    reportYouTubeWatchPage() {
        if (this.currentMedia instanceof YouTubeViewing) {
            // this.youTubeApiLogger.logLandOnPage(this.currentMedia.mediaTitle);
            this.api.youtube.reportYouTubePage(
                this.currentMedia.mediaTitle,
                this.currentMedia.channelName
            );
            return;
        }
        throw new Error("Incorrect media type for YouTube reporting");
    }

    markPlaying() {
        if (!this.currentMedia) {
            throw new MissingMediaError();
        }
        this.currentMedia.playerState = "playing";
        if (this.currentMedia instanceof YouTubeViewing) {
            this.youTubeApiLogger.logPlayEvent();
            const asYouTubePayload = this.currentMedia.convertToPayload();
            console.log("sending play event");
            this.api.youtube.sendPlayEvent(asYouTubePayload);
        } else {
            this.netflixApiLogger.logPlayEvent();
            const asNetflixPayload = this.currentMedia.convertToPayload();
            console.log("sending play event");
            this.api.netflix.sendPlayEvent(asNetflixPayload);
        }
    }

    markPaused() {
        if (!this.currentMedia) {
            throw new MissingMediaError();
        }
        this.currentMedia.playerState = "paused";

        if (this.currentMedia instanceof YouTubeViewing) {
            this.youTubeApiLogger.logPauseEvent();
            const asYouTubePayload = this.currentMedia.convertToPayload();
            console.log("sending pause event");
            this.api.youtube.sendPauseEvent(asYouTubePayload);
        } else {
            this.netflixApiLogger.logPauseEvent();
            const asNetflixPayload = this.currentMedia.convertToPayload();
            console.log("sending pause event");
            this.api.netflix.sendPauseEvent(asNetflixPayload);
        }
    }

    endViewing() {
        // TODO: handle the user closing the tab
        // used to report the final value on window close
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

    convertToPayload(): YouTubePayload {
        return {
            videoId: this.videoId,
            tabTitle: this.mediaTitle,
            channelName: this.channelName,
        };
    }
}

export class NetflixViewingSansState implements IStatelessNetflixViewing {
    videoId: string;
    mediaTitle: string;
    constructor(videoId: string, showName: string) {
        // the Url ID becomes the VideoID.
        this.videoId = videoId;
        // the showName becomes the mediaTitle.
        this.mediaTitle = showName;
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
        playerState: "playing" | "paused"
    ) {
        super(videoId, showName);
        // the Url ID becomes the VideoID.
        this.videoId = videoId;
        // the showName becomes the mediaTitle.
        this.mediaTitle = showName;
        this.playerState = playerState;
    }

    convertToPayload(): NetflixPayload {
        return {
            urlId: this.videoId,
            showName: this.mediaTitle,
            url: "TODO",
            videoId: this.videoId,
        };
    }
}
