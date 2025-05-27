import { vi } from "vitest";
import { ServerApi } from "../src/api";

export function replaceAllMethodsWithMocks(serverConn: ServerApi) {
    serverConn.reportTabSwitch = vi.fn();
    serverConn.reportIgnoredUrl = vi.fn();

    serverConn.youtube.sendYouTubeWatchPage = vi.fn();
    serverConn.youtube.sendPlayEvent = vi.fn();
    serverConn.youtube.sendPauseEvent = vi.fn();
    serverConn.youtube.sendAltTabReturn = vi.fn();

    serverConn.netflix.reportPartialNetflixWatchPage = vi.fn();
    serverConn.netflix.reportFilledNetflixWatchPage = vi.fn();
    serverConn.netflix.sendPlayEvent = vi.fn();
    serverConn.netflix.sendPauseEvent = vi.fn();
    serverConn.netflix.sendAltTabReturn = vi.fn();
}
