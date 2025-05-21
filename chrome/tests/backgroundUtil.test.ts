import { beforeEach, describe, expect, test, vi } from "vitest";
import { ServerApi } from "../src/api.ts";
import { PlayPauseDispatch } from "../src/backgroundUtil.ts";
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
            const tracker = new ViewingTracker(api);
            const someCurrentMedia = new NetflixViewing(
                "123456999",
                "Hilda",
                "paused"
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
            const tracker = new ViewingTracker(api);
            const someCurrentMedia = new NetflixViewing(
                "123456",
                "Hilda",
                "playing"
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
            const tracker = new ViewingTracker(api);

            tracker.markPlaying = vi.fn();

            const dispatch = new PlayPauseDispatch(tracker);

            dispatch.notePlayEvent({});

            expect(tracker.markPlaying).not.toHaveBeenCalledOnce();
        });
    });

    // test("getDomainFromUrl extracts domain correctly", () => {
    //     expect(getDomainFromUrl("www.google.com")).toBe(null);
    //     expect(getDomainFromUrl("https://www.google.com")).toBe(
    //         "www.google.com"
    //     );
    //     expect(getDomainFromUrl("www.youtube.com")).toBe(null);
    //     expect(getDomainFromUrl("https://www.youtube.com")).toBe(
    //         "www.youtube.com"
    //     );
    // });

    // test("isDomainIgnored returns true for ignored domains", () => {
    //     // Set up mock ignored domains
    //     mockIgnoredDomains = ["example.com", "ignored.com"];

    //     expect(isDomainIgnored("example.com", mockIgnoredDomains)).toBe(true);
    //     expect(isDomainIgnored("sub.example.com", mockIgnoredDomains)).toBe(
    //         true
    //     );
    //     expect(isDomainIgnored("notignored.com", mockIgnoredDomains)).toBe(
    //         false
    //     );
    // });
});
