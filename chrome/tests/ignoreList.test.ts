import { describe, expect, test } from "vitest";

import { shouldBeIgnored } from "../src/urlTools";

describe("a variety of user inputs work as intended for the ignore list", () => {
    test("user can type just the domain", () => {
        const theIgnoreList = [
            "google.com",
            "reddit.com",
            "tiktok.com",
            "x.com",
        ];
        expect(shouldBeIgnored("https://mail.google.com", theIgnoreList)).toBe(
            true
        );
        expect(shouldBeIgnored("https://docs.google.com", theIgnoreList)).toBe(
            true
        );
        expect(shouldBeIgnored("https://www.reddit.com", theIgnoreList)).toBe(
            true
        );
        expect(shouldBeIgnored("https://www.tiktok.com", theIgnoreList)).toBe(
            true
        );
        expect(shouldBeIgnored("https://www.x.com", theIgnoreList)).toBe(true);
        expect(shouldBeIgnored("https://www.youtube.com", theIgnoreList)).toBe(
            false
        );
    });
    test("user can type the full domain", () => {
        const theIgnoreList = [
            "https://www.reddit.com",
            "https://www.google.com",
        ];
        expect(shouldBeIgnored("https://mail.google.com", theIgnoreList)).toBe(
            true
        );
        expect(shouldBeIgnored("https://docs.google.com", theIgnoreList)).toBe(
            true
        );
        expect(shouldBeIgnored("https://www.reddit.com", theIgnoreList)).toBe(
            true
        );
    });
    test("user can write it with www", () => {
        // to simplify, if there is no protocol, add the protocol
        const theIgnoreList = [
            "www.reddit.com",
            "www.tiktok.com",
            "www.google.com",
        ];
        expect(shouldBeIgnored("https://mail.google.com", theIgnoreList)).toBe(
            true
        );
        expect(shouldBeIgnored("https://docs.google.com", theIgnoreList)).toBe(
            true
        );
        expect(shouldBeIgnored("https://www.reddit.com", theIgnoreList)).toBe(
            true
        );
        expect(shouldBeIgnored("https://www.tiktok.com", theIgnoreList)).toBe(
            true
        );
        expect(shouldBeIgnored("https://www.youtube.com", theIgnoreList)).toBe(
            false
        );
    });
});
