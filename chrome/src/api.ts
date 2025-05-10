// api.ts

import { PlayerData } from "./interfaces";

const DESKSENSE_BACKEND_URL = "http://localhost:8000";

const chromeTabUrl = "/api/chrome/tab";
const ignoredDomainUrl = "/api/chrome/ignored";
const youTubeUrl = "/api/chrome/youtube/new";

interface YouTubePayload {
    videoId: string;
    tabTitle: string;
    channelName: string;
}
class YouTubeApi {
    sendPayload: Function;
    constructor(sendPayload: Function) {
        this.sendPayload = sendPayload;
    }

    sendPlayEvent({ videoId, tabTitle, channelName }: YouTubePayload) {
        // The server knows which VideoSession it's modifying because
        // the currently active tab deliverable, contained the ...
        console.log("Would send play event for youtugbe");
        const payload = {
            videoId: videoId,
            tabTitle,
            channelName,
            // I don't think I care about the timestamp.
            // Like, what if they did a bunch of rewinding?
            // The timestamp would be messed and not representative of
            // their time spent watching content that day.
            // timestamp: 0
        };
        console.log("The payload would be ", payload);
    }

    sendPauseEvent({ videoId, tabTitle, channelName }: YouTubePayload) {
        console.log("Would send pause event for youtube");
        const payload = {
            videoId,
            tabTitle,
            channelName,
            // timestamp: 0,
        };

        console.log("The pause payload would be ", payload);
    }
}

class NetflixApi {
    sendPayload: Function;
    constructor(sendPayload: Function) {
        this.sendPayload = sendPayload;
    }

    sendPlayEvent() {
        //
    }

    sendPauseEvent() {
        //
    }
}

class ServerApi {
    youtube: YouTubeApi;
    netflix: NetflixApi;

    constructor() {
        this.youtube = new YouTubeApi(this.sendPayload.bind(this));
        this.netflix = new NetflixApi(this.sendPayload.bind(this));
    }

    reportTabSwitch(domain: string, tabTitle: string) {
        const payload = {
            url: domain, // Must match the pydantic definition
            tabTitle: tabTitle,
            startTime: new Date(),
        };
        console.log("Sending payload:", payload);
        this.sendPayload(chromeTabUrl, payload);
    }

    reportYouTube(
        tabTitle: string | undefined,
        channel: string,
        playerData?: PlayerData
    ) {
        /* Tab title must be undefined sometimes, says TS */
        console.log("[info] Channel " + channel);
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
        this.sendPayload(youTubeUrl, payload);
    }

    reportNetflix(foo: string, bar: string) {
        // TODO
        console.log("Reporting netflix is not supported yet");
    }

    reportIgnoredUrl() {
        const payload = {
            url: "ignored", // Must match the pydantic definition
            tabTitle: "ignored",
            startTime: new Date(),
        };
        console.log("Sending payload:", payload);
        this.sendPayload(ignoredDomainUrl, payload);
    }

    private sendPayload(targetUrl: string, payload: object) {
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
                    console.log("Validation Error Details:", response.json());
                } else {
                    throw new Error(
                        `Request failed with status ${response.status}`
                    );
                }
            })
            .catch((error) => console.error("Error:", error));
    }
}

export const api = new ServerApi();
