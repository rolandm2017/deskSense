import { describe, expect, test } from "vitest";

import { WatchEntry } from "../../src/netflix/historyRecorder";
import {
    RankScores,
    TopFiveAlgorithm,
} from "../../src/netflix/topFiveAlgorithm";

describe("Top five algorithm", () => {
    describe("Recency scoring", () => {
        describe("The exponential decay function", () => {
            const algorithm = new TopFiveAlgorithm([]);
            test("Zero hours ago", () => {
                const d = algorithm.exponentialDecay(0);
                expect(d).toBe(1);
            });
            test("One hour ago", () => {
                const v = algorithm.exponentialDecay(1);
                expect(parseFloat(v.toFixed(3))).toBe(0.99);
            });
            test("Five hours ago", () => {
                const d = algorithm.exponentialDecay(5);
                expect(parseFloat(d.toFixed(3))).toBe(0.951);
            });
            test("Twenty-four hours ago", () => {
                const v = algorithm.exponentialDecay(24);
                expect(parseFloat(v.toFixed(3))).toBe(0.787);
            });
            test("Three days prior", () => {
                const d = algorithm.exponentialDecay(72);
                expect(parseFloat(d.toFixed(3))).toBe(0.487);
            });
            test("Seven days prior", () => {
                const v = algorithm.exponentialDecay(168);
                expect(parseFloat(v.toFixed(3))).toBe(0.186);
            });
        });
        describe("Single viewings in the full recency method", () => {
            const now = Date.now();
            const oneHourAsMilliseconds = 3600000; // (1000 * 60 * 60)

            test("Five hours ago", () => {
                const showTimestamps = [now - oneHourAsMilliseconds * 5];
                const score = new TopFiveAlgorithm([]).computeRecencyScore(
                    showTimestamps,
                    now
                );
                console.log(score.toFixed(2));

                expect(parseFloat(score.toFixed(2))).toBe(95.12);
            });
            test("Twenty-four hours ago", () => {
                const showTimestamps = [now - oneHourAsMilliseconds * 24];
                const score = new TopFiveAlgorithm([]).computeRecencyScore(
                    showTimestamps,
                    now
                );
                console.log(score.toFixed(2));
                expect(parseFloat(score.toFixed(2))).toBe(78.66);
            });
            test("Three days prior", () => {
                const showTimestamps = [now - oneHourAsMilliseconds * 72];
                const score = new TopFiveAlgorithm([]).computeRecencyScore(
                    showTimestamps,
                    now
                );
                console.log(score.toFixed(2));
                expect(parseFloat(score.toFixed(2))).toBe(48.68);
            });
            test("Nine days prior", () => {
                const showTimestamps = [
                    now - oneHourAsMilliseconds * 216, // 9 days ago
                ];
                const score = new TopFiveAlgorithm([]).computeRecencyScore(
                    showTimestamps,
                    now
                );
                console.log(score.toFixed(2));
                expect(parseFloat(score.toFixed(2))).toBe(11.53);
            });
        });
        test("One viewing a week ago scores low", () => {
            const now = Date.now();
            const oneHour = 1000 * 60 * 60;
            const showTimestamps = [
                now - oneHour * 216, // 9 days ago
            ];
            const score = new TopFiveAlgorithm([]).computeRecencyScore(
                showTimestamps,
                now
            );
            console.log(score.toFixed(2));
            expect(score).toBeDefined();
            expect(parseFloat(score.toFixed(2))).toBe(11.53);
        });
        test("Ten viewings a week ago scores higher", () => {
            const now = Date.now();
            const oneHour = 1000 * 60 * 60;
            const showTimestamps = [
                now - oneHour * 212, // 9 days ago
                now - oneHour * 213, // 9 days ago and an hour
                now - oneHour * 214, // 9 days ago
                now - oneHour * 215, // 9 days ago
                now - oneHour * 216, // 9 days ago
                now - oneHour * 217, // 9 days ago
                now - oneHour * 218, // 9 days ago and a few hours
            ];
            const score = new TopFiveAlgorithm([]).computeRecencyScore(
                showTimestamps,
                now
            );
            console.log(score.toFixed(2));
            expect(score).toBeDefined();
            expect(parseFloat(score.toFixed(2))).toBe(11.65);
        });

        test("Ten viewings a week ago and ten viewings yesterday scores really high", () => {
            const now = Date.now();
            const oneHour = 1000 * 60 * 60;
            const showTimestamps = [
                now - oneHour * 212, // 9 days ago
                now - oneHour * 213, // 9 days ago
                now - oneHour * 214, // 9 days ago
                now - oneHour * 215, // 9 days ago
                now - oneHour * 216, // 9 days ago
                now - oneHour * 217, // 9 days ago
                now - oneHour * 218, // 9 days ago
                now - oneHour * 25, // 1 day + 1 hours ago
                now - oneHour * 26, // 1 day + 2 hours ago
                now - oneHour * 27, // 1 day + 3 hours ago
                now - oneHour * 28, // 1 day + 4 hours ago
            ];
            const score = new TopFiveAlgorithm([]).computeRecencyScore(
                showTimestamps,
                now
            );
            console.log(score.toFixed(2));
            expect(score).toBeDefined();
            expect(parseFloat(score.toFixed(2))).toBe(35.31);
        });
        test("Three quite recent viewings and two old viewings", () => {
            const now = Date.now();
            const oneHour = 1000 * 60 * 60;
            const showTimestamps = [
                now - oneHour * 1, // 1 hour ago
                now - oneHour * 2, // 2 hours ago
                now - oneHour * 25, // 1 day + 1 hour ago
                now - oneHour * 192, // 8 days ago
                now - oneHour * 216, // 9 days ago
            ];

            const score = new TopFiveAlgorithm([]).computeRecencyScore(
                showTimestamps,
                now
            );
            console.log(score.toFixed(2));
            expect(score).toBeDefined();
            expect(parseFloat(score.toFixed(2))).toBe(60.22);
        });
        test("Scores increase with recency and frequency", () => {
            const now = Date.now();
            const oneHour = 1000 * 60 * 60;
            const algo = new TopFiveAlgorithm([]);

            // Scenario 1: One viewing a week ago
            const timestamps1 = [now - oneHour * 216]; // 9 days ago
            const score1 = algo.computeRecencyScore(timestamps1, now);
            expect(score1).toBeGreaterThan(0.01);

            // Scenario 2: Multiple viewings a week ago
            const timestamps2 = Array(7)
                .fill(0)
                .map((_, i) => now - oneHour * (212 + i));
            const score2 = algo.computeRecencyScore(timestamps2, now);
            expect(score1).toBeGreaterThan(0.01);

            // Scenario 3: Viewings last week and yesterday
            const timestamps3 = [
                ...timestamps2,
                ...[25, 26, 27, 28].map((h) => now - oneHour * h),
            ];
            const score3 = algo.computeRecencyScore(timestamps3, now);
            expect(score1).toBeGreaterThan(0.01);

            // Scenario 4: Recent viewings (1-2 hours ago) + mixed
            const timestamps4 = [
                now - oneHour * 1,
                now - oneHour * 2,
                now - oneHour * 25,
                now - oneHour * 192,
                now - oneHour * 216,
            ];
            const score4 = algo.computeRecencyScore(timestamps4, now);
            expect(score1).toBeGreaterThan(0.01);

            // Assert progression
            expect(score1).toBeLessThan(score2);
            expect(score2).toBeLessThan(score3);
            expect(score3).toBeLessThan(score4);

            // Log for debugging
            console.log({
                score1: score1.toFixed(2),
                score2: score2.toFixed(2),
                score3: score3.toFixed(2),
                score4: score4.toFixed(2),
            });
        });
    });

    describe("Frequency scoring", () => {
        // If you ask why frequency scoring's tests are so short,
        // it's because it's literally count / total.
        const algorithm = new TopFiveAlgorithm([]);
        test("One hit from two returns 0.5", () => {
            const input = [
                { showName: "Hilda" } as WatchEntry,
                { showName: "Some Other Show" } as WatchEntry,
            ];
            const score = algorithm.getRawFrequencyScore("Hilda", input);
            expect(score).toBe(0.5);
        });
        test("Two hits from five returns 0.4", () => {
            const input = [
                { showName: "Hilda" } as WatchEntry,
                { showName: "Hilda" } as WatchEntry,
                { showName: "Some Other Show" } as WatchEntry,
                { showName: "Some Other Show" } as WatchEntry,
                { showName: "Some Other Show" } as WatchEntry,
            ];
            const score = algorithm.getRawFrequencyScore("Hilda", input);
            expect(score).toBe(0.4);
        });
        test("Five hits from twenty returns 0.25", () => {
            const input = [
                ...Array(5).fill({ showName: "Hilda" } as WatchEntry),
                ...Array(15).fill({
                    showName: "Some Other Show",
                } as WatchEntry),
            ];
            const score = algorithm.getRawFrequencyScore("Hilda", input);
            expect(score).toBe(0.25);
        });
    });
    describe("Compute novelty", () => {
        const algo = new TopFiveAlgorithm([]);
        describe("Pure math utils", () => {
            describe("getPositionOnCircle", () => {
                // TODO: Refactor so it's really all in one, not two funcs
                // Can check vals yourself using a calculator
                // y = sqrt(1 - x^2)
                test("Fifty percent gives y", () => {
                    const expectedY = 0.8660254037844386;
                    expect(algo.getPositionOnCircle(0.5)).toBe(expectedY);
                });
                test("Twenty-five percent gives y", () => {
                    const expectedY = 0.9682458365518543;
                    expect(algo.getPositionOnCircle(0.25)).toBe(expectedY);
                });
                test("Ten percent gives y", () => {
                    const expectedY = 0.99498743710662;
                    expect(algo.getPositionOnCircle(0.1)).toBe(expectedY);
                });
            });
            test("getAdjustmentWithAverage", () => {
                expect(algo.getAdjustmentWithAverage(8, 4)).toBe(6);
                expect(algo.getAdjustmentWithAverage(0, 10)).toBe(5);
            });
        });
        describe("getFirstSeenDateFor", () => {
            test("Works with one entry", () => {
                const title = "Hilda";
                const now = new Date();
                const oneFullDay = 86400000; // 24 * 60 * 60 * 1000
                const dates = [
                    new Date(now.getTime() - 3 * oneFullDay),
                    new Date(now.getTime() - 5 * oneFullDay),
                    new Date(now.getTime() - 8 * oneFullDay),
                ];
                const allHistory: WatchEntry[] = [
                    {
                        showName: title,
                        timestamp: dates[0].toISOString(),
                    } as WatchEntry,
                    {
                        showName: title,
                        timestamp: dates[1].toISOString(),
                    } as WatchEntry,
                    {
                        showName: title,
                        timestamp: dates[2].toISOString(),
                    } as WatchEntry,
                ] as WatchEntry[];
                expect(
                    algo.getFirstSeenDateFor(title, allHistory)
                ).toStrictEqual(dates[2]);
            });
        });
        describe("hoursBetween", () => {
            const algorithm = new TopFiveAlgorithm([]);
            test("returns 0 for same date", () => {
                const date = new Date("2025-05-11T12:00:00Z");
                expect(algorithm.hoursBetween(date, date)).toBe(0);
            });

            test("returns 24 for dates 24 hours apart", () => {
                const date1 = new Date("2025-05-11T12:00:00Z");
                const date2 = new Date("2025-05-12T12:00:00Z");
                expect(algorithm.hoursBetween(date1, date2)).toBe(24);
            });

            test("returns same result regardless of date order", () => {
                const date1 = new Date("2025-05-11T12:00:00Z");
                const date2 = new Date("2025-05-12T12:00:00Z");
                expect(algorithm.hoursBetween(date1, date2)).toBe(
                    algorithm.hoursBetween(date2, date1)
                );
            });

            test("handles fractional hours correctly", () => {
                const date1 = new Date("2025-05-11T12:00:00Z");
                const date2 = new Date("2025-05-11T15:30:00Z");
                expect(algorithm.hoursBetween(date1, date2)).toBe(3.5);
            });
        });
    });

    describe("Group entries by title", () => {
        const algo = new TopFiveAlgorithm([]);
        test("Entries are grouped by title", () => {
            const input = [
                { showName: "Hilda" } as WatchEntry,
                { showName: "Hilda" } as WatchEntry,
                { showName: "Some Other Show" } as WatchEntry,
                { showName: "Some Other Show" } as WatchEntry,
                { showName: "Some Other Show" } as WatchEntry,
                { showName: "Lupin" } as WatchEntry,
                { showName: "Lupin" } as WatchEntry,
                { showName: "Carmen San Diego" } as WatchEntry,
                { showName: "Carmen San Diego" } as WatchEntry,
            ];
            const result = algo.groupEntriesByTitle(input);

            expect(result).toEqual(
                expect.objectContaining({
                    Hilda: expect.arrayContaining([
                        expect.objectContaining({ showName: "Hilda" }),
                    ]),
                    "Some Other Show": expect.arrayContaining([
                        expect.objectContaining({
                            showName: "Some Other Show",
                        }),
                    ]),
                    Lupin: expect.arrayContaining([
                        expect.objectContaining({ showName: "Lupin" }),
                    ]),
                    "Carmen San Diego": expect.arrayContaining([
                        expect.objectContaining({
                            showName: "Carmen San Diego",
                        }),
                    ]),
                })
            );

            // Check array lengths
            expect(result["Hilda"].length).toBe(2);
            expect(result["Some Other Show"].length).toBe(3);
            expect(result["Lupin"].length).toBe(2);
            expect(result["Carmen San Diego"].length).toBe(2);
        });
        test("Grouping works with just one type of title", () => {
            //
        });
        test("Grouping returns an empty obj for empty arrays", () => {
            //
        });
    });
    describe("Get top five titles", () => {
        const algo = new TopFiveAlgorithm([]);

        test("Actually gets the top five", () => {
            const someScores: RankScores = {
                Foo: { score: 1, recency: 0 },
                Bar: { score: 2, recency: 0 },
                Baz: { score: 3, recency: 0 },
                Hilda: { score: 5, recency: 0 },
                "The Hollow": { score: 6, recency: 0 },
                "The Three Body Problem": { score: 10, recency: 0 },
                "Carmen San Diego": { score: 11, recency: 0 },
                Lupin: { score: 9, recency: 0 },
                "L'Agence": { score: 8, recency: 0 },
            };
            const ranked = algo.getTopFiveTitles(someScores);
            expect(ranked).toEqual([
                "Carmen San Diego",
                "The Three Body Problem",
                "Lupin",
                "L'Agence",
                "The Hollow",
            ]);
        });

        test("Breaks ties using recency score", () => {
            const someScores: RankScores = {
                Foo: { score: 1, recency: 0 },
                Bar: { score: 2, recency: 0 },
                Baz: { score: 3, recency: 0 },
                Hilda: { score: 9, recency: 0.1 },
                "The Three Body Problem": { score: 10, recency: 0 },
                "L'Agence": { score: 9, recency: 0.4 },
                Lupin: { score: 9, recency: 0.3 },
                "The Hollow": { score: 9, recency: 0.2 },
                "Carmen San Diego": { score: 11, recency: 0 },
            };
            const ranked = algo.getTopFiveTitles(someScores);
            expect(ranked).toEqual([
                "Carmen San Diego",
                "The Three Body Problem",
                "L'Agence", // These four all have score: 9,
                "Lupin", // but are sorted by recency
                "The Hollow", // in descending order
            ]);
        });

        test("Works for only three inputs", () => {
            const justThree: RankScores = {
                Hilda: { score: 5, recency: 0 },
                "The Three Body Problem": { score: 10, recency: 0 },
                Lupin: { score: 9, recency: 0 },
            };
            const ranked = algo.getTopFiveTitles(justThree);
            expect(ranked).toEqual([
                "The Three Body Problem",
                "Lupin",
                "Hilda",
            ]);
        });
    });
});
