// api.ts
import { DomainLogger, PlatformLogger } from "./endpointLogging";
import {
    AltTabNetflixReturn,
    AltTabYouTubeReturn,
    NetflixPayload,
    YouTubePayload,
} from "./interface/interfaces";
import {
    NetflixPlayerChange,
    NetflixTabChange,
    YouTubePlayerChange,
    YouTubeTabChange,
} from "./interface/payloads";
import { NetflixViewing } from "./videoCommon/visits";

const DESKSENSE_BACKEND_URL = "http://localhost:8000";

const baseChromeUrl = "/api/chrome";

export const chromeTabUrl = baseChromeUrl + "/tab";
export const ignoredDomainUrl = baseChromeUrl + "/ignored";

const videoBaseUrl = baseChromeUrl + "/video";

export const youTubeRoutes = {
    youTubeWatchPageUrl: videoBaseUrl + "/youtube/new/watchpage",
    youtubePlayerStateUrl: videoBaseUrl + "/youtube/state",
    altTabYouTubeWatchUrl: videoBaseUrl + "/youtube/alt-tab-return",
};

export const netflixRoutes = {
    netflixWatchPageUrl: videoBaseUrl + "/netflix/new/watchpage",
    netflixPlayerStateUrl: videoBaseUrl + "/netflix/state",
    altTabNetflixWatchUrl: videoBaseUrl + "/netflix/alt-tab-return",
};

class YouTubeApi {
    sendPayload: Function;
    logger: PlatformLogger;
    logging: boolean;

    constructor(sendPayload: Function, logging: boolean) {
        this.sendPayload = sendPayload;
        this.logging = logging;
        this.logger = new PlatformLogger("YouTube");
    }

    // NOTE: a regular youTube page != a youTube Watch Page

    sendYouTubeWatchPage(
        tabTitle: string | undefined,
        videoId: string,
        channel: string,
        initialPlayerState: "playing" | "paused"
    ) {
        /* Tab title must be undefined sometimes, says TS */
        const payload: YouTubeTabChange = {
            url: "www.youtube.com",
            videoId,
            tabTitle: tabTitle ?? "Unknown Tab Title",
            channel,
            startTime: new Date().toISOString(),
            playerState: initialPlayerState,
        };
        console.log("Sending YouTube Watch Page payload:", payload.channel);
        // console.log(youTubeUrl, "is the youtube url");
        this.sendPayload(youTubeRoutes.youTubeWatchPageUrl, payload);
    }
    // TODO:
    // Refreshing a Youtube Watch page should be something like,
    // (1) First, something tries to get the channel, AND/OR
    // end up calling the reportYouTubePage function.
    // (2) Simultaneously, it expects the playing state to arrive momentarily.
    // Only when (1) and (2) are both satisfied, THEN a POST is sent,
    // saying "here is the page and btw it's playing"
    // PROBLEM: Can't have Player State, then Page. Bad! Will cause problems.
    // Page, then Player State might be ok. With like a 300 ms delay.

    sendPlayEvent({ videoId, tabTitle, channelName, url }: YouTubePayload) {
        // The server knows which VideoSession it's modifying because
        // the currently active tab deliverable, contained the ...
        const payload: YouTubePlayerChange = {
            url,
            videoId: videoId,
            tabTitle,
            channel: channelName,
            eventTime: new Date().toISOString(),

            playerState: "playing",
            // I don't think I care about the timestamp.
            // Like, what if they did a bunch of rewinding?
            // The timestamp would be messed and not representative of
            // their time spent watching content that day.
            // timestamp: 0
        };
        console.log("The play payload is ", payload.channel);
        this.sendPayload(youTubeRoutes.youtubePlayerStateUrl, payload);
    }

    sendPauseEvent({ videoId, tabTitle, channelName, url }: YouTubePayload) {
        const payload: YouTubePlayerChange = {
            url,
            videoId,
            tabTitle,
            channel: channelName,
            eventTime: new Date().toISOString(),
            playerState: "paused",
            // timestamp: 0,
        };
        console.log("The pause payload is ", payload.channel);
        this.sendPayload(youTubeRoutes.youtubePlayerStateUrl, payload);
    }

    sendAltTabReturn(payload: AltTabYouTubeReturn) {
        console.log("Sending YouTube alt-tab return payload:", payload.channel);
        this.sendPayload(youTubeRoutes.altTabYouTubeWatchUrl, payload);
    }
}

class NetflixApi {
    sendPayload: Function;
    logger: PlatformLogger;
    logging: boolean;

    constructor(sendPayload: Function, logging: boolean) {
        this.sendPayload = sendPayload;
        this.logging = logging;
        this.logger = new PlatformLogger("Netflix");
    }

    reportPartialNetflixWatchPage(
        fullUrl: string,
        watchPageId: string,
        playerState: "playing" | "paused"
    ) {
        // It's only the watchPageId because that's the only
        // thing that doesn't require waiting for user input.
        const payload: NetflixTabChange = {
            tabTitle: "Unknown Watch Page",
            url: fullUrl,
            videoId: watchPageId,
            startTime: new Date().toISOString(),
            playerState,
        };
        this.sendPayload(netflixRoutes.netflixWatchPageUrl, payload);
    }

    reportFilledNetflixWatchPage({
        videoId,
        mediaTitle,
        playerState,
    }: NetflixViewing) {
        const payload: NetflixTabChange = {
            tabTitle: mediaTitle,
            videoId,
            url: "https://www.netflix.com/watch/" + videoId,
            playerState: playerState,
            startTime: new Date().toISOString(),
        };
        // I guess if the server receives an update, it can propagate the
        // updated info to all logs related to that previously mysterious ID
        this.sendPayload(netflixRoutes.netflixWatchPageUrl, payload);
    }

    // TODO: If they select the wrong thing form the dropdown,
    // TODO: AND they hit Confirm,
    // then they can just open the modal again, select the right value,
    // click Confirm. And the program will end the incorrect session,
    // start them on the right one. They lose 2-3 min tracked in
    // the wrong spot.
    sendPlayEvent({ videoId, showName }: NetflixPayload) {
        // The server knows which VideoSession it's modifying because
        // the currently active tab deliverable, contained the ...
        console.log("Would send play event for Netflix");
        const payload: NetflixPlayerChange = {
            tabTitle: showName,
            url: "https://www.netflix.com/watch/" + videoId,
            videoId: videoId,
            showName,
            eventTime: new Date().toISOString(),

            playerState: "playing",
            // I don't care about the timestamp.
            // Like, what if they did a bunch of rewinding?
            // The timestamp would be messed and not representative of
            // their time spent watching content that day.
            // timestamp: 0
        };
        console.log("The play payload is ", payload);
        this.sendPayload(netflixRoutes.netflixPlayerStateUrl, payload);
    }

    sendPauseEvent({ videoId, showName }: NetflixPayload) {
        // TODO: Align inputs definitions in chrome/api and server.py

        this.logger.logPauseEvent(showName);
        console.log("Would send pause event for Netflix");
        const payload: NetflixPlayerChange = {
            videoId,
            url: "https://www.netflix.com/watch/" + videoId,
            tabTitle: showName,
            showName,
            eventTime: new Date().toISOString(),

            playerState: "paused",
        };

        console.log("The pause payload is ", payload);
        this.sendPayload(netflixRoutes.netflixPlayerStateUrl, payload);
    }

    sendAltTabReturn(payload: AltTabNetflixReturn) {
        console.log(
            "Sending Netflix alt-tab return payload:",
            payload.showName
        );
        this.sendPayload(netflixRoutes.altTabNetflixWatchUrl, payload);
    }
}

export class ServerApi {
    youtube: YouTubeApi;
    netflix: NetflixApi;
    enablePayloads: boolean;
    logger: DomainLogger;
    logging: boolean;

    constructor(enablePayloads: "enable" | "disable") {
        // Must set disablePayloads = false, deliberately. To protect testers
        this.enablePayloads = enablePayloads === "enable";
        if (this.enablePayloads) {
            console.log("Payloads are enabled");
        }
        this.logging = false;
        this.youtube = new YouTubeApi(
            this.sendPayload.bind(this),
            this.logging
        );
        this.netflix = new NetflixApi(
            this.sendPayload.bind(this),
            this.logging
        );
        this.logger = new DomainLogger();
    }

    reportTabSwitch = (domain: string, tabTitle: string) => {
        const payload = {
            url: domain, // Must match the pydantic definition
            tabTitle: tabTitle,
            startTime: new Date(),
        };
        // console.log("Sending tab switch payload:", payload);
        this.sendPayload(chromeTabUrl, payload);
    };

    reportIgnoredUrl = () => {
        const payload = {
            url: "ignored", // Must match the pydantic definition
            tabTitle: "ignored",
            startTime: new Date(),
        };
        console.log("Sending ignoredUrl payload:", payload);
        this.sendPayload(ignoredDomainUrl, payload);
    };

    sendPayload = (targetUrl: string, payload: object) => {
        if (!this.enablePayloads) {
            console.log("Sending payloads is disabled");
            return;
        }

        fetch(DESKSENSE_BACKEND_URL + targetUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        })
            .then((response) => {
                // Note there is no JSON in a 204

                // console.log("Status Code:", response.status) // Log the status code
                if (response.status === 204) {
                    // console.log("payload received")
                } else if (response.status == 422) {
                    console.log("Retrieving error json");
                    response.json().then((r) => {
                        // Make sure we're logging the actual error data, not a pending Promise
                        console.log(
                            "[err response] Validation Error Details for " +
                                targetUrl,
                            JSON.stringify(r, null, 2)
                        );
                    });
                } else {
                    throw new Error(
                        `Request failed with status ${response.status}`
                    );
                }
            })
            .catch((error) => console.error("Error:", error));
    };

    replacePayloadMethod(newMethod: any) {
        // You think the any is a bad idea, but replacing it is worse
        // Made just for inserting mocks
        this.sendPayload = newMethod;
        this.youtube.sendPayload = newMethod;
        this.netflix.sendPayload = newMethod;
    }
}

export const initializedServerApi = new ServerApi("enable");
