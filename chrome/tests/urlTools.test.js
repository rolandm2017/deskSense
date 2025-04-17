import { removeBeforeWww, stripProtocol, normalizeUrl } from "../src/urlTools"

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
