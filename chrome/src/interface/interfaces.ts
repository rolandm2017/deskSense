export interface PlayerData {
    timestamp: number;
    state: "playing" | "paused";
}
export interface YouTubePayload {
    videoId: string;
    tabTitle: string;
    channelName: string;
}

export interface NetflixPayload {
    urlId: string;
    videoId: string;
    showName: string;
    url: string;
}

export interface WatchEntry {
    serverId: number; //
    urlId: string;
    showName: string;
    url: string;
    timestamp: string; // new Date().isoString()
    msTimestamp: number; // generated automatically (by the code)
    watchCount: number; // count of times it was watched
}

//  these are mostly here to enable expedited comparison with their payloads
export interface IYouTubeViewing {
    videoId: string;
    mediaTitle: string;
    timestamps: number[];
    playerState: "playing" | "paused";
    // unique to this class
    channelName: string;
}

export interface INetflixViewing {
    videoId: string;
    mediaTitle: string;
    timestamps: number[];
    playerState: "playing" | "paused";
}
