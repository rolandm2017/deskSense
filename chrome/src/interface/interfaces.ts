// interfaces.ts

import { YouTubeViewing } from "../videoCommon/visits";

export interface Task {
    type: string;
    data?: DomainInfo | ChannelOnly | YouTubeViewing;
}

export interface ChannelOnly {
    channelName: string;
}

export interface DomainInfo {
    domain: string;
    tabTitle: string;
}

export interface YouTubePayload {
    url: string;
    videoId: string;
    tabTitle: string;
    channelName: string;
}

export interface NetflixPayload {
    videoId: string;
    showName: string;
}

export interface AltTabYouTubeReturn {
    url: string;
    videoId: string;
    tabTitle: string;
    channel: string;
    returnTime: string; // ISO timestamp when user alt-tabbed back
    playerState: "playing" | "paused";
    // Optionally include context about where they came from
    previousContext?: "external_app" | "other_chrome_tab";
}

export interface AltTabNetflixReturn {
    url: string;
    videoId: string;
    tabTitle: string;
    showName: string;
    returnTime: string;
    playerState: "playing" | "paused";
    previousContext?: "external_app" | "other_chrome_tab";
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
    playerState: "playing" | "paused";
    // unique to this class
    channelName: string;
}

export interface IStatelessNetflixViewing {
    videoId: string;
    mediaTitle: string;
}

export interface INetflixViewing extends IStatelessNetflixViewing {
    playerState: "playing" | "paused";
}
