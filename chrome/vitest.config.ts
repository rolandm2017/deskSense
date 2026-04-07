import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        environment: "playwright",
        include: [
            "src/**/*.{test,spec}.{js,ts}",
            "tests/**/*.{test,spec}.{js,ts}",
        ],
        globals: true,
    },
});
