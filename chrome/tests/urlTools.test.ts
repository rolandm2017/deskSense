import { describe, expect, it, test } from "vitest";

import {
    getBaseDomain,
    normalizeUrl,
    removeBeforeWww,
    shouldBeIgnored,
    stripProtocol,
} from "../src/urlTools";

describe("URL Tools behave as expected", () => {
    it("removes the www from the URL", () => {
        expect(removeBeforeWww("https://www.google.com")).toBe(
            "www.google.com"
        );
    });
    it("Strips the protocol", () => {
        expect(stripProtocol("https://www.google.com")).toBe("www.google.com");
        expect(stripProtocol("http://www.shady.com")).toBe("www.shady.com");
    });
    it("Normalizes the URL", () => {
        expect(normalizeUrl("https://www.google.com")).toBe("google.com");
        expect(normalizeUrl("https://www.youtube.com")).toBe("youtube.com");
        expect(normalizeUrl("https://mail.google.com")).toBe("mail.google.com");
        expect(normalizeUrl("https://docs.google.com")).toBe("docs.google.com");
    });
});

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
            "https://www.tiktok.com",
            "https://www.x.com",
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
        expect(shouldBeIgnored("https://www.tiktok.com", theIgnoreList)).toBe(
            true
        );
        expect(shouldBeIgnored("https://www.x.com", theIgnoreList)).toBe(true);
        expect(shouldBeIgnored("https://www.youtube.com", theIgnoreList)).toBe(
            false
        );
    });
    test("user can write it with www", () => {
        // to simplify, if there is no protocol, add the protocol
        const theIgnoreList = [
            "www.reddit.com",
            "www.tiktok.com",
            "www.x.com",
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
        expect(shouldBeIgnored("https://www.x.com", theIgnoreList)).toBe(true);
        expect(shouldBeIgnored("https://www.youtube.com", theIgnoreList)).toBe(
            false
        );
    });
});

describe("our PSL replacement performs adequately", () => {
    test("basic domains", () => {
        expect(getBaseDomain("youtube.com")).toBe("youtube.com");
        expect(getBaseDomain("google.com")).toBe("google.com");
        expect(getBaseDomain("php.net")).toBe("php.net");
        expect(getBaseDomain("sourceforge.net")).toBe("sourceforge.net");
        expect(getBaseDomain("wikipedia.org")).toBe("wikipedia.org");
        expect(getBaseDomain("mayoclinic.org")).toBe("mayoclinic.org");
    });
    test("domains with www", () => {
        expect(getBaseDomain("www.youtube.com")).toBe("youtube.com");
        expect(getBaseDomain("www.google.com")).toBe("google.com");
        expect(getBaseDomain("www.php.net")).toBe("php.net");
        expect(getBaseDomain("www.sourceforge.net")).toBe("sourceforge.net");
        expect(getBaseDomain("www.wikipedia.org")).toBe("wikipedia.org");
        expect(getBaseDomain("www.mayoclinic.org")).toBe("mayoclinic.org");
    });
    test("full URLs with protocol", () => {
        expect(getBaseDomain("https://www.youtube.com")).toBe("youtube.com");
        expect(getBaseDomain("https://mail.google.com")).toBe("google.com");
        expect(getBaseDomain("https://subdomain.news.com.au")).toBe(
            "news.com.au"
        );
    });
    test("URLS that have the path still", () => {
        expect(
            getBaseDomain("https://www.youtube.com/watch?v=93Sfl5rRBGw")
        ).toBe("youtube.com");
        expect(getBaseDomain("https://www.lemonde.fr/en/united-states/")).toBe(
            "lemonde.fr"
        );
        expect(
            getBaseDomain("https://travelblog.blogspot.com/2023/05/my-trip")
        ).toBe("blogspot.com");
    });
    test("strange cases going right from protocol -> subdomain", () => {
        //
        expect(
            getBaseDomain("https://docs.google.com/document/u/0/?pli=1")
        ).toBe("google.com");
        expect(getBaseDomain("https://mail.google.com/mail/u/0/#inbox")).toBe(
            "google.com"
        );
        expect(getBaseDomain("http://bbc.co.uk/news")).toBe("bbc.co.uk");
        expect(getBaseDomain("https://username.github.io/project")).toBe(
            "github.io"
        );
    });

    test("urls that have more .'s than usual still work", () => {
        expect(getBaseDomain("https://www.news.com.au/entertainment")).toBe(
            "news.com.au"
        );
    });
});
