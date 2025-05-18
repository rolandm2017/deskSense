import { describe, expect, it, test } from "vitest";

import {
    getBaseDomain,
    normalizeUrl,
    removeBeforeWww,
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

describe("our getBaseDomain PSL replacement performs adequately", () => {
    test("basic domains", () => {
        expect(getBaseDomain("youtube.com")).toBe("youtube.com");
        expect(getBaseDomain("google.com")).toBe("google.com");
        expect(getBaseDomain("php.net")).toBe("php.net");
        expect(getBaseDomain("sourceforge.net")).toBe("sourceforge.net");
        expect(getBaseDomain("wikipedia.org")).toBe("wikipedia.org");
        expect(getBaseDomain("mayoclinic.org")).toBe("mayoclinic.org");
    });
    test("domains with www", () => {
        // If domain starts with "www.", remove it, fwd to usual func.
        expect(getBaseDomain("www.youtube.com")).toBe("youtube.com");
        expect(getBaseDomain("www.google.com")).toBe("google.com");
        expect(getBaseDomain("www.php.net")).toBe("php.net");
        expect(getBaseDomain("www.sourceforge.net")).toBe("sourceforge.net");
        expect(getBaseDomain("www.wikipedia.org")).toBe("wikipedia.org");
        expect(getBaseDomain("www.mayoclinic.org")).toBe("mayoclinic.org");
    });
    test("full URLs with protocol", () => {
        // If domain starts with "https://www." or "http://", remove it, fwd to the www func.

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
        // ax off https://, go to "handle subdomain"
        expect(
            getBaseDomain("https://docs.google.com/document/u/0/?pli=1")
        ).toBe("google.com");
        expect(getBaseDomain("https://mail.google.com/mail/u/0/#inbox")).toBe(
            "google.com"
        );
        // NOTE that I don't know what better thing to do here for the bbc,
        // where the subdomain bbc.co.uk is very much a part of the recognizability
        expect(getBaseDomain("https://bbc.co.uk/news")).toBe("co.uk");
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
