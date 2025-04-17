import { beforeEach, vi } from "vitest"

// Create a mock Chrome API
global.chrome = {
    tabs: {
        onCreated: {
            addListener: vi.fn(),
        },
        onUpdated: {
            addListener: vi.fn(),
        },
        onActivated: {
            addListener: vi.fn(),
        },
        get: vi.fn(),
    },
    storage: {
        local: {
            get: vi.fn(),
            set: vi.fn(),
        },
        onChanged: {
            addListener: vi.fn(),
        },
    },
    runtime: {
        onInstalled: {
            addListener: vi.fn(),
        },
        openOptionsPage: vi.fn(),
    },
    action: {
        onClicked: {
            addListener: vi.fn(),
        },
    },
}

// Reset mocks before each test
beforeEach(() => {
    vi.clearAllMocks()
})
