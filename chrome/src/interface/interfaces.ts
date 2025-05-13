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
