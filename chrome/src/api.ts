// api.ts
import { DomainLogger, PlatformLogger } from "./endpointLogging";
import {
    NetflixPayload,
    PlayerData,
    YouTubePayload,
} from "./interface/interfaces";

const DESKSENSE_BACKEND_URL = "http://localhost:8000";

const baseChromeUrl = "/api/chrome";

export const chromeTabUrl = baseChromeUrl + "/tab";
export const ignoredDomainUrl = baseChromeUrl + "/ignored";

// youtube
export const youTubeUrl = baseChromeUrl + "/video/youtube/new";
export const youtubePlayerStateUrl = baseChromeUrl + "/video/youtube/state";
// netflix
export const netflixUrl = baseChromeUrl + "/video/netflix/new";
export const netflixPlayerStateUrl = baseChromeUrl + "/video/netflix/state";

export const captureSessionStartUrl = "/api/capture/start";

class YouTubeApi {
    sendPayload: Function;
    logger: PlatformLogger;
    logging: boolean;

    constructor(sendPayload: Function, logging: boolean) {
        this.sendPayload = sendPayload;
        this.logging = logging;
        this.logger = new PlatformLogger("YouTube");
    }

    reportYouTubePage(
        tabTitle: string | undefined,
        channel: string,
        playerData?: PlayerData
    ) {
        /* Tab title must be undefined sometimes, says TS */
        const payload = {
            // Uses the YouTubeEvent pydantic definition
            url: "www.youtube.com",
            tabTitle,
            channel,
            startTime: new Date(),
            playerPositionInSec: 1000,
        };
        // console.log("Sending YouTube Page payload:", payload);
        // console.log(youTubeUrl, "is the youtube url");
        if (this.logging) {
            this.logger.logLandOnPage(tabTitle ?? "Unknown Tab");
            this.logger.logPayloadToStorage(
                "reportYouTubePage",
                youTubeUrl,
                payload
            );
        }
        this.sendPayload(youTubeUrl, payload);
    }

    sendPlayEvent({ videoId, tabTitle, channelName }: YouTubePayload) {
        // The server knows which VideoSession it's modifying because
        // the currently active tab deliverable, contained the ...
        const payload = {
            videoId: videoId,
            tabTitle,
            channel: channelName,
            eventTime: new Date(),

            playerState: "playing",
            // I don't think I care about the timestamp.
            // Like, what if they did a bunch of rewinding?
            // The timestamp would be messed and not representative of
            // their time spent watching content that day.
            // timestamp: 0
        };
        // console.log("The play payload was be ", payload);
        if (this.logging) {
            this.logger.logPlayEvent(tabTitle);
            this.logger.logPayloadToStorage(
                "sendPlayEvent",
                youtubePlayerStateUrl,
                payload
            );
        }
        this.sendPayload(youtubePlayerStateUrl, payload);
    }

    sendPauseEvent({ videoId, tabTitle, channelName }: YouTubePayload) {
        const payload = {
            videoId,
            tabTitle,
            channel: channelName,
            eventTime: new Date(),
            playerState: "paused",
            // timestamp: 0,
        };
        if (this.logging) {
            this.logger.logPauseEvent(tabTitle);
            this.logger.logPayloadToStorage(
                "sendPause",
                youtubePlayerStateUrl,
                payload
            );
        }
        // console.log("The pause payload was be ", payload);
        this.sendPayload(youtubePlayerStateUrl, payload);
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

    reportNetflixPage(videoId: string) {
        // TODO

        if (this.logging) {
            this.logger.logLandOnPage(videoId ?? "Unknown Media");
            console.log("Reporting netflix is not supported yet", videoId);

            this.logger.logPayloadToStorage("reportNetflixPage", netflixUrl, {
                videoId,
            });
        }
        this.sendPayload(netflixUrl, { videoId });
    }

    // TODO: If they select the wrong thing form the dropdown,
    // TODO: AND they hit Confirm,
    // then they can just open the modal again, select the right value,
    // click Confirm. And the program will end the incorrect session,
    // start them on the right one. They lose 2-3 min tracked in
    // the wrong spot.
    sendPlayEvent({ urlId, showName }: NetflixPayload) {
        // The server knows which VideoSession it's modifying because
        // the currently active tab deliverable, contained the ...
        console.log("Would send play event for Netflix");
        const payload = {
            urlId,
            showName,
            eventTime: new Date(),

            playerState: "playing",
            // I don't think I care about the timestamp.
            // Like, what if they did a bunch of rewinding?
            // The timestamp would be messed and not representative of
            // their time spent watching content that day.
            // timestamp: 0
        };
        // console.log("The play payload was be ", payload);
        if (this.logging) {
            this.logger.logPayloadToStorage(
                "sendPlayEvent",
                netflixPlayerStateUrl,
                payload
            );
        }
        this.sendPayload(netflixPlayerStateUrl, payload);
    }

    sendPauseEvent({ urlId, showName }: NetflixPayload) {
        // TODO: Align inputs definitions in chrome/api and server.py

        this.logger.logPauseEvent(showName);
        console.log("Would send pause event for Netflix");
        const payload = {
            urlId,
            showName,
            eventTime: new Date(),

            playerState: "paused",
        };

        // console.log("The pause payload was be ", payload);
        if (this.logging) {
            this.logger.logPayloadToStorage(
                "sendPlayEvent",
                netflixPlayerStateUrl,
                payload
            );
        }
        this.sendPayload(netflixPlayerStateUrl, payload);
    }
}

export class ServerApi {
    youtube: YouTubeApi;
    netflix: NetflixApi;
    disablePayloads: boolean;
    logger: DomainLogger;
    logging: boolean;

    constructor(disablePayloads: boolean = true) {
        // Must set disablePayloads = false, deliberately. To protect testers
        this.disablePayloads = disablePayloads;
        if (this.disablePayloads === false) {
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
        console.log("Sending tab switch payload:", payload);
        if (this.logging) {
            this.logger.logPayloadToStorage(
                "reportTabSwitch",
                chromeTabUrl,
                payload
            );
        }
        this.sendPayload(chromeTabUrl, payload);
    };

    reportIgnoredUrl = () => {
        const payload = {
            url: "ignored", // Must match the pydantic definition
            tabTitle: "ignored",
            startTime: new Date(),
        };
        console.log("Sending ignoredUrl payload:", payload);
        if (this.logging) {
            this.logger.logPayloadToStorage(
                "reportIgnoredUrl",
                ignoredDomainUrl,
                payload
            );
        }
        this.sendPayload(ignoredDomainUrl, payload);
    };

    checkForCaptureSession(setStartTimeCallback: Function) {
        fetch(DESKSENSE_BACKEND_URL + captureSessionStartUrl, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        }).then((response) => {
            setStartTimeCallback(response);
        });
    }

    sendPayload = (targetUrl: string, payload: object) => {
        if (this.disablePayloads) {
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
        this.sendPayload = newMethod;
        this.youtube.sendPayload = newMethod;
        this.netflix.sendPayload = newMethod;
    }
}

export const initializedServerApi = new ServerApi(true);
