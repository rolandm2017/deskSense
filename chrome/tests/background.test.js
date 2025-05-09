import { beforeEach, describe, expect, test, vi } from "vitest";
import { getDomainFromUrl, isDomainIgnored } from "../src/background.js";

// Mock the imported functions
vi.mock("../src/api.js", () => ({
    reportTabSwitch: vi.fn(),
    reportIgnoredUrl: vi.fn(),
}));

// Mock global functions from background.js
// We'll need to either expose them or use a different approach
let mockIsdomainIgnored;
let mockGetDomainFromUrl;
let mockIgnoredDomains = [];

describe("Background Script", () => {
    beforeEach(() => {
        // Reset mock data
        mockIgnoredDomains = [];
    });

    test("getDomainFromUrl extracts domain correctly", () => {
        expect(getDomainFromUrl("www.google.com")).toBe(null);
        expect(getDomainFromUrl("https://www.google.com")).toBe(
            "www.google.com"
        );
        expect(getDomainFromUrl("www.youtube.com")).toBe(null);
        expect(getDomainFromUrl("https://www.youtube.com")).toBe(
            "www.youtube.com"
        );
    });

    test("isDomainIgnored returns true for ignored domains", () => {
        // Set up mock ignored domains
        mockIgnoredDomains = ["example.com", "ignored.com"];

        expect(isDomainIgnored("example.com", mockIgnoredDomains)).toBe(true);
        expect(isDomainIgnored("sub.example.com", mockIgnoredDomains)).toBe(
            true
        );
        expect(isDomainIgnored("notignored.com", mockIgnoredDomains)).toBe(
            false
        );
    });
});
