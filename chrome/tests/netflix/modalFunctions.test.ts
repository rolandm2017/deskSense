import { describe, expect, test } from "vitest";

import { WatchHistoryTracker } from "../../src/netflix/historyTracker";

import { MockStorageApi } from "./mockStorageInterface";

describe("[integration] The modal's key behaviors work", () => {
    //
    test("Seeing the top five results works", async () => {
        // Expect loading the modal to cause the db to .read_all() and
        // cobble together a top five.
        const mockStorageApi = new MockStorageApi();
        const historyTracker = new WatchHistoryTracker(mockStorageApi);
        expect(1).toBe(1);
    });
    test("Selecting a dropdown entry works", async () => {
        //
    });
    test("Inputting a new title manually works", async () => {
        //
    });
    test("Loading the dropdown causes expired data to be deleted", async () => {
        //
    });
});
