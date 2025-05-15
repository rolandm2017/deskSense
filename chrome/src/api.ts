// api.ts
import { DomainLogger, PlatformLogger } from "./endpointLogging";
import {
    NetflixPayload,
    PlayerData,
    YouTubePayload,
} from "./interface/interfaces";

const DESKSENSE_BACKEND_URL = "http://localhost:8000";

const chromeTabUrl = "/api/chrome/tab";
const ignoredDomainUrl = "/api/chrome/ignored";
// youtube
const youTubeUrl = "/api/chrome/youtube/new";
const youtubePlayerStateUrl = "/api/chrome/youtube/state";
// netflix
const netflixUrl = "/api/chrome/netflix/new";
const netflixPlayerStateUrl = "/api/chrome/netflix/state";

const captureSessionStartUrl = "/api/capture/start";

class YouTubeApi {
    sendPayload: Function;
    logger: PlatformLogger;

    constructor(sendPayload: Function) {
        this.sendPayload = sendPayload;
        this.logger = new PlatformLogger("YouTube");
    }

    reportYouTubePage(
        tabTitle: string | undefined,
        channel: string,
        playerData?: PlayerData
    ) {
        /* Tab title must be undefined sometimes, says TS */
        this.logger.logLandOnPage(tabTitle ?? "Unknown Tab");
        const payload = {
            // Uses the YouTubeEvent pydantic definition
            url: "www.youtube.com",
            tabTitle,
            channel,
            startTime: new Date(),
            playerPositionInSec: 1000,
        };
        console.log("Sending YouTube payload:", payload);
        console.log(youTubeUrl, "is the youtube url");
        this.logger.logPayloadToStorage(
            "reportYouTubePage",
            youTubeUrl,
            payload
        );
        this.sendPayload(youTubeUrl, payload);
    }

    sendPlayEvent({ videoId, tabTitle, channelName }: YouTubePayload) {
        // The server knows which VideoSession it's modifying because
        // the currently active tab deliverable, contained the ...
        this.logger.logPlayEvent(tabTitle);
        const payload = {
            videoId: videoId,
            tabTitle,
            channel: channelName,
            playerState: "playing",
            // I don't think I care about the timestamp.
            // Like, what if they did a bunch of rewinding?
            // The timestamp would be messed and not representative of
            // their time spent watching content that day.
            // timestamp: 0
        };
        console.log("The play payload was be ", payload);
        this.logger.logPayloadToStorage(
            "sendPlayEvent",
            youtubePlayerStateUrl,
            payload
        );
        this.sendPayload(youtubePlayerStateUrl, payload);
    }

    sendPauseEvent({ videoId, tabTitle, channelName }: YouTubePayload) {
        this.logger.logPauseEvent(tabTitle);
        const payload = {
            videoId,
            tabTitle,
            channel: channelName,
            playerState: "paused",
            // timestamp: 0,
        };
        this.logger.logPayloadToStorage(
            "sendPause",
            youtubePlayerStateUrl,
            payload
        );
        // console.log("The pause payload was be ", payload);
        this.sendPayload(youtubePlayerStateUrl, payload);
    }
}

class NetflixApi {
    sendPayload: Function;
    logger: PlatformLogger;

    constructor(sendPayload: Function) {
        this.sendPayload = sendPayload;
        this.logger = new PlatformLogger("Netflix");
    }

    reportNetflixPage(mediaTitle: string) {
        // TODO
        this.logger.logLandOnPage(mediaTitle ?? "Unknown Media");
        console.log("Reporting netflix is not supported yet", mediaTitle);

        this.logger.logPayloadToStorage("reportNetflixPage", netflixUrl, {
            mediaTitle,
        });
    }

    // TODO: If they select the wrong thing form the dropdown,
    // TODO: AND they hit Confirm,
    // then they can just open the modal again, select the right value,
    // click Confirm. And the program will end the incorrect session,
    // start them on the right one. They lose 2-3 min tracked in
    // the wrong spot.
    sendPlayEvent({ urlId, showName, url }: NetflixPayload) {
        // The server knows which VideoSession it's modifying because
        // the currently active tab deliverable, contained the ...
        console.log("Would send play event for Netflix");
        const payload = {
            urlId,
            showName,
            url,
            playerState: "playing",
            // I don't think I care about the timestamp.
            // Like, what if they did a bunch of rewinding?
            // The timestamp would be messed and not representative of
            // their time spent watching content that day.
            // timestamp: 0
        };
        console.log("The play payload was be ", payload);
        this.sendPayload(youtubePlayerStateUrl, payload);
        this.logger.logPayloadToStorage(
            "sendPlayEvent",
            netflixPlayerStateUrl,
            payload
        );
    }

    sendPauseEvent({ urlId, showName, url }: NetflixPayload) {
        this.logger.logPauseEvent(showName);
        console.log("Would send pause event for Netflix");
        const payload = {
            urlId,
            showName,
            url,
            playerState: "paused",
        };

        console.log("The pause payload was be ", payload);
        this.logger.logPayloadToStorage(
            "sendPlayEvent",
            netflixPlayerStateUrl,
            payload
        );
        this.sendPayload(youtubePlayerStateUrl, payload);
    }
}

export class ServerApi {
    youtube: YouTubeApi;
    netflix: NetflixApi;
    disablePayloads: boolean;
    logger: DomainLogger;

    constructor() {
        this.disablePayloads = true;
        this.youtube = new YouTubeApi(this.sendPayload.bind(this));
        this.netflix = new NetflixApi(this.sendPayload.bind(this));
        this.logger = new DomainLogger();
    }

    reportTabSwitch = (domain: string, tabTitle: string) => {
        const payload = {
            url: domain, // Must match the pydantic definition
            tabTitle: tabTitle,
            startTime: new Date(),
        };
        console.log("Sending payload:", payload);
        this.logger.logPayloadToStorage(
            "reportTabSwitch",
            chromeTabUrl,
            payload
        );
        this.sendPayload(chromeTabUrl, payload);
    };

    reportIgnoredUrl = () => {
        const payload = {
            url: "ignored", // Must match the pydantic definition
            tabTitle: "ignored",
            startTime: new Date(),
        };
        console.log("Sending payload:", payload);
        this.logger.logPayloadToStorage(
            "reportIgnoredUrl",
            ignoredDomainUrl,
            payload
        );
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

    private sendPayload = (targetUrl: string, payload: object) => {
        if (this.disablePayloads) {
            console.log("Sending payloads is disabled");
            return;
        }
        console.log(this.disablePayloads, "207ru");

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
}

export const api = new ServerApi();
