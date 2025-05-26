import { beforeEach, describe, expect, test, vi } from "vitest";
import { ServerApi } from "../src/api.ts";
import { PlayPauseDispatch } from "../src/backgroundUtil.ts";
import { PlayerStateCache } from "../src/playerStateCache.ts";
import { NetflixViewing, ViewingTracker } from "../src/videoCommon/visits.ts";
import { replaceAllMethodsWithMocks } from "./helper.ts";

// Mock global functions from background.js
// We'll need to either expose them or use a different approach
let mockIsdomainIgnored;
let mockGetDomainFromUrl;
let mockIgnoredDomains = [];

describe("Background Util", () => {
    beforeEach(() => {
        // Reset mock data
        mockIgnoredDomains = [];
    });

    describe("PlayPauseDispatch", () => {
        test("Note Play Event marks the tracker media as playing", () => {
            const api = new ServerApi("disable");
            // turn off send payloads
            replaceAllMethodsWithMocks(api);
            const cache = new PlayerStateCache();
            const tracker = new ViewingTracker(cache, api);
            const someCurrentMedia = new NetflixViewing(
                "123456999",
                "netflix.com/watch/123456999",

                "Hilda",
                "paused",
                9000
            );
            tracker.setCurrent(someCurrentMedia);
            tracker.markPlaying = vi.fn();

            const dispatch = new PlayPauseDispatch(tracker);

            dispatch.notePlayEvent({});

            expect(tracker.markPlaying).toHaveBeenCalledOnce();
        });
        test("Note Pause Event marks the tracker media as paused", () => {
            const api = new ServerApi("disable");
            // turn off send payloads
            replaceAllMethodsWithMocks(api);
            const cache = new PlayerStateCache();
            const tracker = new ViewingTracker(cache, api);
            const someCurrentMedia = new NetflixViewing(
                "123456",
                "netflix.com/watch/123456",
                "Hilda",
                "playing",
                9000
            );
            tracker.setCurrent(someCurrentMedia);
            tracker.markPlaying = vi.fn();
            tracker.markPaused = vi.fn();

            const dispatch = new PlayPauseDispatch(tracker);

            dispatch.notePauseEvent();

            expect(tracker.markPaused).toHaveBeenCalledOnce();
        });
        test("If the viewing tracker has no current media, nothing happens", () => {
            const api = new ServerApi("disable");

            // turn off send payloads
            replaceAllMethodsWithMocks(api);

            const cache = new PlayerStateCache();
            const tracker = new ViewingTracker(cache, api);

            tracker.markPlaying = vi.fn();

            const dispatch = new PlayPauseDispatch(tracker);

            dispatch.notePlayEvent({});

            expect(tracker.markPlaying).not.toHaveBeenCalledOnce();
        });
    });
});
