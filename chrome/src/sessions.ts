// sessions.ts
import { pollingInterval } from "./channelExtractor";

class SessionTracker {
    /*
     * Class is a container enabling cross-file session management.
     */
    current: YouTubeSession | NetflixSession | undefined;

    constructor() {
        this.current = undefined;
    }

    setCurrent(current: YouTubeSession | NetflixSession) {
        if (this.current) {
            if (this.current instanceof YouTubeSession) {
                // report old session
                console.log("[debug] Reporting YouTube session");
                // api.reportYouTube("TODO", "TODO");
            } else {
                console.log("[debug] Reporting Netflix session");
                // api.reportNetflix("TODO", "TODO");
            }
        }
        this.current = current;
    }

    concludeSession() {
        // used to report the final value on window close
    }
}

export const sessionTracker = new SessionTracker();

export class NetflixSession {
    // TODO
    tabTitle: string;
    contentTitle: string;
    timestamps: number[];

    constructor(tabTitle: string, contentTitle: string) {
        this.tabTitle = tabTitle;
        this.contentTitle = contentTitle;
        this.timestamps = [];
    }

    addTimestamp(timestamp: number) {
        this.timestamps.push(timestamp);
    }

    isStillPlaying() {
        const previous = this.timestamps.at(-2);
        const current = this.timestamps.at(-1);
        if (previous && current) {
            const gap = previous - current;
            const stillPlaying = gap === pollingInterval;
            if (stillPlaying) {
                // still playing
            } else {
                // paused
            }
        }
    }
}

export class YouTubeSession {
    videoId: string;
    tabTitle: string;
    channelName: string;
    timestamps: number[];
    playerState: "playing" | "paused";

    constructor(videoId: string, tabTitle: string, channelName: string) {
        this.videoId = videoId;
        this.tabTitle = tabTitle;
        this.channelName = channelName;
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
        // if the session lasted 60 sec, report it and start fresh.
    }

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
}
