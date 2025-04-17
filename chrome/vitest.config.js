import { defineConfig } from "vitest/config"

export default defineConfig({
    test: {
        environment: "happy-dom", // or 'jsdom'
        globals: true,
        setupFiles: ["./vitest.setup.js"],
    },
})
