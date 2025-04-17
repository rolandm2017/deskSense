import {
    removeBeforeWww,
    shouldBeIgnored,
    stripProtocol,
    normalizeUrl,
} from "../src/urlTools"

describe("URL Tools behave as expected", () => {
    it("removes the www from the URL", () => {
        expect(removeBeforeWww("https://www.google.com")).toBe("www.google.com")
    })
    it("Strips the protocol", () => {
        expect(stripProtocol("https://www.google.com")).toBe("www.google.com")
        expect(stripProtocol("http://www.shady.com")).toBe("www.shady.com")
    })
    it("Normalizes the URL", () => {
        expect(normalizeUrl("https://www.google.com")).toBe("google.com")
        expect(normalizeUrl("https://www.youtube.com")).toBe("youtube.com")
        expect(normalizeUrl("https://mail.google.com")).toBe("mail.google.com")
        expect(normalizeUrl("https://docs.google.com")).toBe("docs.google.com")
    })
})

describe("a variety of user inputs work as intended for the ignore list", () => {
    test("user can type just the domain", () => {
        const theIgnoreList = [
            "google.com",
            "reddit.com",
            "tiktok.com",
            "x.com",
        ]
        expect(shouldBeIgnored("https://mail.google.com", theIgnoreList)).toBe(
            true
        )
        expect(shouldBeIgnored("https://docs.google.com", theIgnoreList)).toBe(
            true
        )
        expect(shouldBeIgnored("https://www.reddit.com", theIgnoreList)).toBe(
            true
        )
        expect(shouldBeIgnored("https://www.tiktok.com", theIgnoreList)).toBe(
            true
        )
        expect(shouldBeIgnored("https://www.x.com", theIgnoreList)).toBe(true)
        expect(shouldBeIgnored("https://www.youtube.com", theIgnoreList)).toBe(
            false
        )
    })
    test("user can type the full domain", () => {
        const theIgnoreList = [
            "https://www.reddit.com",
            "https://www.tiktok.com",
            "https://www.x.com",
            "https://www.google.com",
        ]
        expect(shouldBeIgnored("https://mail.google.com", theIgnoreList)).toBe(
            true
        )
        expect(shouldBeIgnored("https://docs.google.com", theIgnoreList)).toBe(
            true
        )
        expect(shouldBeIgnored("https://www.reddit.com", theIgnoreList)).toBe(
            true
        )
        expect(shouldBeIgnored("https://www.tiktok.com", theIgnoreList)).toBe(
            true
        )
        expect(shouldBeIgnored("https://www.x.com", theIgnoreList)).toBe(true)
        expect(shouldBeIgnored("https://www.youtube.com", theIgnoreList)).toBe(
            false
        )
    })
    test("user can write it with www", () => {
        // to simplify, if there is no protocol, add the protocol
        const theIgnoreList = [
            "www.reddit.com",
            "www.tiktok.com",
            "www.x.com",
            "www.google.com",
        ]
        expect(shouldBeIgnored("https://mail.google.com", theIgnoreList)).toBe(
            true
        )
        expect(shouldBeIgnored("https://docs.google.com", theIgnoreList)).toBe(
            true
        )
        expect(shouldBeIgnored("https://www.reddit.com", theIgnoreList)).toBe(
            true
        )
        expect(shouldBeIgnored("https://www.tiktok.com", theIgnoreList)).toBe(
            true
        )
        expect(shouldBeIgnored("https://www.x.com", theIgnoreList)).toBe(true)
        expect(shouldBeIgnored("https://www.youtube.com", theIgnoreList)).toBe(
            false
        )
    })
})
