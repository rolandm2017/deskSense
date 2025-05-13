import { vi } from "vitest";

export function replaceAllMethodsWithMocks(serverConn) {
    serverConn.youtube.reportYouTubePage = vi.fn();
    serverConn.youtube.sendPlayEvent = vi.fn();
    serverConn.youtube.sendPauseEvent = vi.fn();
    serverConn.netflix.reportNetflixPage = vi.fn();
    serverConn.netflix.sendPlayEvent = vi.fn();
    serverConn.netflix.sendPauseEvent = vi.fn();
}
