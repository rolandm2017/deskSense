import { beforeEach, describe, expect, test, vi } from "vitest";
import { ServerApi } from "../src/api.ts";
import { getTaskForDomain, PlayPauseDispatch } from "../src/backgroundUtil.ts";
import { taskTypes } from "../src/const.ts";
import { ignoredDomains } from "../src/ignoreList.ts";
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

    describe("getTaskForDomain returns appropriate types", () => {
        // handleYouTubeUrl paths handled in youtube.test.ts

        test("Regular domains return the Regular Domain task type", () => {
            const url = "https://www.wikipedia.org";
            const tab = { url, id: 9020 } as chrome.tabs.Tab;

            const task = getTaskForDomain(tab, (foo) => {
                //
            });

            expect(task).toBeDefined();
            expect(task!.type).toBe(taskTypes.REGULAR_DOMAIN);
        });
        test("Getting the domain from an ignored URL reports an ignored URL", () => {
            const url = "https://www.google.com";

            ignoredDomains.addNew(url);

            const tab = { url, id: 9021 } as chrome.tabs.Tab;

            const task = getTaskForDomain(tab, (foo) => {
                //
            });

            expect(task).toBeDefined();

            expect(task!.type).toBe(taskTypes.IGNORED_URL);

            ignoredDomains.reset();
        });
        test("Netflix Watch pages return the Netflix Watch Page type", () => {
            const url = "https://www.netflix.com/watch/23403284";
            const tab = { url, id: 9022 } as chrome.tabs.Tab;

            const task = getTaskForDomain(tab, (foo) => {
                //
            });

            expect(task).toBeDefined();
            expect(task!.type).toBe(taskTypes.NETFLIX_WATCH_PAGE);
        });
        // handleYouTubeUrl paths handled in youtube.test.ts
    });

    describe("PlayPauseDispatch", () => {
        test("Note Play Event marks the tracker media as playing", () => {
            const api = new ServerApi("disable");
            // turn off send payloads
            replaceAllMethodsWithMocks(api);

            const tracker = new ViewingTracker(api);
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

            const tracker = new ViewingTracker(api);
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

            const tracker = new ViewingTracker(api);

            tracker.markPlaying = vi.fn();

            const dispatch = new PlayPauseDispatch(tracker);

            dispatch.notePlayEvent({});

            expect(tracker.markPlaying).not.toHaveBeenCalledOnce();
        });
    });
});
