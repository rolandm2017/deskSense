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
    latestActiveViewing: YouTubeViewing | NetflixViewing | undefined;
    mostRecentReport: YouTubeViewing | undefined;
    autoplayWaiting: boolean;
    stateCache: Map<number, YouTubeViewing | NetflixViewing>;
    api: ServerApi;

    partialNetflixDescriptor: string | undefined;

    constructor(api: ServerApi) {
        this.stateCache = new Map<number, YouTubeViewing | NetflixViewing>();
        this.api = api;
        this.mostRecentReport = undefined;
        this.latestActiveViewing = undefined;
        this.autoplayWaiting = false;
        this.currentMedia = undefined;
        this.partialNetflixDescriptor = undefined;

        // TODO: JUST ASSUME it's going to work with Play/Pause only,
        // until you figure out otherwise.
    }

    setCurrent(current: YouTubeViewing | NetflixViewing) {
        this.currentMedia = current;
        this.stateCache.set(current.sourceTabId, current);
    }

    markAutoplayEventWaiting() {
        // Don't send the play event right away like usual.
        // Instead, note that one is waiting to be delivered,
        // and bundle it in with the Watch Page report.
        this.autoplayWaiting = true;
    }

    reportInitialLandOnWatchPage() {
        if (this.currentMedia instanceof YouTubeViewing) {
            // use autoplay state
            this.reportYouTubeWatchPage(
                this.autoplayWaiting ? "playing" : "paused"
            );
        }
    }

    reportTabBackIntoWatchPage() {
        if (this.currentMedia instanceof YouTubeViewing) {
            this.reportYouTubeWatchPage(this.currentMedia.playerState);
        }
    }

    reportYouTubeWatchPage(playerState: "playing" | "paused") {
        // FIXME: It's the case that, when you refresh, the
        // NewPageLoad event (this thing) goes off, BUT the video is playing!
        // And there is no notification of it BEING playing! No indication.

        if (this.currentMedia instanceof YouTubeViewing) {
            this.mostRecentReport = this.currentMedia;
            this.api.youtube.sendYouTubeWatchPage(
                this.currentMedia.mediaTitle,
                this.currentMedia.videoId,
                this.currentMedia.channelName,
                playerState
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
        // TODO: PAUSE and Play Needs to update the cached player state

        this.currentMedia.playerState = "playing";
        this.updateCachedState(this.currentMedia);

        console.log("sending play event");
        if (this.currentMedia instanceof YouTubeViewing) {
            const asYouTubePayload = this.currentMedia.convertToPayload();
            this.api.youtube.sendPlayEvent(asYouTubePayload);
        } else {
            const asNetflixPayload = this.currentMedia.convertToPayload();
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
        this.updateCachedState(this.currentMedia);
    }

    markPaused() {
        if (!this.currentMedia) {
            throw new MissingMediaError();
        }
        // TODO: PAUSE and Play Needs to update the cached player state
        this.currentMedia.playerState = "paused";
        this.updateCachedState(this.currentMedia);

        console.log("sending pause event");
        if (this.currentMedia instanceof YouTubeViewing) {
            const asYouTubePayload = this.currentMedia.convertToPayload();
            this.api.youtube.sendPauseEvent(asYouTubePayload);
        } else {
            const asNetflixPayload = this.currentMedia.convertToPayload();
            this.api.netflix.sendPauseEvent(asNetflixPayload);
        }
    }

    updateCachedState(update: YouTubeViewing | NetflixViewing) {
        this.stateCache.set(update.sourceTabId, update);
    }

    hasPlayerStateForTab(tabId: number) {
        return this.stateCache.has(tabId);
    }

    useStoredPlayerState(tabId: number) {
        return this.stateCache.get(tabId)!;
    }

    endViewing(tabId: number) {
        // TODO: handle the user closing the tab
        // used to report the final value on window close
        this.stateCache.delete(tabId);
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
    playerState: "playing" | "paused";
    // unique to this class
    channelName: string;
    sourceTabId: number;

    // Can tell also *how long* player was paused for.

    constructor(
        videoId: string,
        url: string,
        tabTitle: string,
        channelName: string,
        sourceTabId: number
    ) {
        this.videoId = videoId;
        this.url = url;
        this.mediaTitle = tabTitle;
        this.channelName = channelName;
        this.sourceTabId = sourceTabId;
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
        // It cannot have a SourceTabID because
        // there is no tabId accessible in a content script.
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
    // videoId: string;
    // mediaTitle: string;
    playerState: "playing" | "paused";
    sourceTabId: number;
    // TODO
    constructor(
        videoId: string,
        showName: string,
        url: string,
        playerState: "playing" | "paused",
        sourceTabId: number
    ) {
        super(videoId, showName, url);
        // the Url ID becomes the VideoID.
        // this.videoId = videoId;
        // the showName becomes the mediaTitle.
        // this.mediaTitle = showName;
        this.playerState = playerState;
        this.sourceTabId = sourceTabId;
    }

    convertToPayload(): NetflixPayload {
        return {
            showName: this.mediaTitle,
            videoId: this.videoId,
        };
    }
}
