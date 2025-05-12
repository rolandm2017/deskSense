import { describe, expect, test } from "vitest";

import { TopFiveAlgorithm } from "../../src/netflix/topFiveAlgorithm";

describe("Top five algorithm", () => {
    describe("The exponential decay function", () => {
        const algorithm = new TopFiveAlgorithm();
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
    describe("Single viewings passed to the full recency score method", () => {
        const now = Date.now();
        const oneHourAsMilliseconds = 3600000; // (1000 * 60 * 60)

        test("Five hours ago", () => {
            const showTimestamps = [now - oneHourAsMilliseconds * 5];
            const score = new TopFiveAlgorithm().computeRecencyScore(
                showTimestamps,
                now
            );
            console.log(score.toFixed(2));

            expect(parseFloat(score.toFixed(2))).toBe(95.12);
        });
        test("Twenty-four hours ago", () => {
            const showTimestamps = [now - oneHourAsMilliseconds * 24];
            const score = new TopFiveAlgorithm().computeRecencyScore(
                showTimestamps,
                now
            );
            console.log(score.toFixed(2));
            expect(parseFloat(score.toFixed(2))).toBe(78.66);
        });
        test("Three days prior", () => {
            const showTimestamps = [now - oneHourAsMilliseconds * 72];
            const score = new TopFiveAlgorithm().computeRecencyScore(
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
            const score = new TopFiveAlgorithm().computeRecencyScore(
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
        const score = new TopFiveAlgorithm().computeRecencyScore(
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
            now - oneHour * 213, // 9 days ago
            now - oneHour * 214, // 9 days ago
            now - oneHour * 215, // 9 days ago
            now - oneHour * 216, // 9 days ago
            now - oneHour * 217, // 9 days ago
            now - oneHour * 218, // 9 days ago
        ];
        const score = new TopFiveAlgorithm().computeRecencyScore(
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
        const score = new TopFiveAlgorithm().computeRecencyScore(
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

        const score = new TopFiveAlgorithm().computeRecencyScore(
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
        const algo = new TopFiveAlgorithm();

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
