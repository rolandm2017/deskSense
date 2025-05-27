import { describe, expect, test, vi } from "vitest";

import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

// Get current file's directory and go up to chrome/
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const chromeDir = join(__dirname, "../..");

// Read and parse the JSON file
const payloadLogFilePath = join(
    chromeDir,
    "logs",
    "payload-events-Tue May 27 2025.json"
);
const rawData = readFileSync(payloadLogFilePath, "utf8");
const payloadEvents = JSON.parse(rawData);

const activityLogFilePath = join(
    chromeDir,
    "logs",
    "user-input-activity-Tue May 27 2025 (2).json"
);
const rawUserData = readFileSync(activityLogFilePath, "utf8");
const userEvents = JSON.parse(rawUserData);

describe("Run the system according to a set of recorded user inputs", () => {
    //
    test("System responds in the same way it did last time", () => {
        //
        for (const event of userEvents) {
            console.log(event.type);
        }
        const mock = vi.fn();
        expect(1).toBe(1);
    });
});
