// ALT_TAB_BACK_IN
// PLAYER_STATE_CHANGED
// ON_UPDATED_COMPLETE

import { AltTabYouTubeReturn } from "../interface/interfaces";
import { YouTubePlayerChange, YouTubeTabChange } from "../interface/payloads";

export type CaptureEvent =
    | { type: "ON_UPDATED_COMPLETE"; data: OnUpdatedData; metadata: Metadata }
    | {
          type: "PLAYER_STATE_CHANGED";
          data: PlayerStateData;
          metadata: Metadata;
      }
    | { type: "ALT_TAB_BACK_IN"; data: AltTabData; metadata: Metadata }
    | { type: "TAB_CLOSED"; data: TabClosedData; metadata: Metadata }
    | { type: "TEST_CAPTURE"; data: object; metadata: Metadata };
// Add more cases here as needed

export interface OnUpdatedData {
    tabId: number;
    url: string;
}

export interface PlayerStateData {
    message: {
        type: string;
        event: string;
    };
    sender: {
        tab?: {
            url?: string;
        };
    };
}

export interface AltTabData {
    id: number;
    url: string;
    title?: string;
}

export interface TabClosedData {
    tabId: number;
}

export interface Metadata {
    source: string;
    method: string;
    location: string;
    timestamp: string;
}

export interface PayloadCaptureEvent {
    type: string; // e.g., "sendPlayEvent"
    data: {
        payload: YouTubeTabChange | YouTubePlayerChange | AltTabYouTubeReturn;
        url: string;
    };
    metadata: Metadata;
}

export function isOnUpdatedCompleteEvent(event: CaptureEvent): event is {
    type: "ON_UPDATED_COMPLETE";
    data: OnUpdatedData;
    metadata: Metadata;
} {
    return event.type === "ON_UPDATED_COMPLETE";
}

export function isPlayerStateChangedEvent(event: CaptureEvent): event is {
    type: "PLAYER_STATE_CHANGED";
    data: PlayerStateData;
    metadata: Metadata;
} {
    return event.type === "PLAYER_STATE_CHANGED";
}

export function isAltTabBackInEvent(
    event: CaptureEvent
): event is { type: "ALT_TAB_BACK_IN"; data: AltTabData; metadata: Metadata } {
    return event.type === "ALT_TAB_BACK_IN";
}

export function isTabClosedEvent(
    event: CaptureEvent
): event is { type: "TAB_CLOSED"; data: TabClosedData; metadata: Metadata } {
    return event.type === "TAB_CLOSED";
}
