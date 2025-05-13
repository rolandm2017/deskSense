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
