import { describe, expect, test } from "vitest";
// Test will fail unless import is done
import "../mocks/chrome"; // Import the mock

import { DayHistory, WatchEntry } from "../../src/netflix/history";
import { readAll, readDay, saveDay } from "../../src/netflix/storageApi";

describe("The storage layer can persist data", () => {
    //
    test("Storing an item works", async () => {
        const entryOne: WatchEntry = {
            showName: "Hilda",
            videoId: "83u492384u32",
            url: "netflix.com/watch/3408932432",
            watchCount: 1,
            timestamp: new Date().toISOString(),
        };
        const entryTwo: WatchEntry = {
            showName: "Hilda Season 2",
            videoId: "jfa8fd3p9",
            url: "netflix.com/watch/58932450982",

            timestamp: new Date().toISOString(),
            watchCount: 2,
        };

        const testDay: DayHistory = {
            "2025-05-12": [entryOne, entryTwo],
        };

        await saveDay(testDay);

        const results = await readAll();

        expect(results).toBeDefined();

        expect(results.length).toBe(2);
    });
    test("Taking an item out works", async () => {
        const entryOne: WatchEntry = {
            showName: "Hilda",
            videoId: "83u492384u32",
            url: "netflix.com/watch/3408932432",
            watchCount: 1,
            timestamp: new Date().toISOString(),
        };
        const entryTwo: WatchEntry = {
            showName: "Hilda Season 2",
            videoId: "jfa8fd3p9",
            url: "netflix.com/watch/58932450982",

            timestamp: new Date().toISOString(),
            watchCount: 2,
        };

        const testDay: DayHistory = {
            "2025-05-12": [entryOne, entryTwo],
        };

        await saveDay(testDay);

        const dayKey = Object.keys(testDay)[0];

        const results = await readDay[dayKey];

        expect(results).toBeDefined();

        expect(results.length).toBe(2);
    });
});
