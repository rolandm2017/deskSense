// chrome/tests/mocks/chrome.ts
const createStorageArea = () => ({
    get: (keys: any, callback: (result: any) => void) => {
        const mockData = {
            watchHistory: {},
            "2025-05-12": [],
        };

        if (typeof keys === "string") {
            callback({ [keys]: mockData[keys] });
        } else if (Array.isArray(keys)) {
            const result = {};
            keys.forEach((key) => {
                result[key] = mockData[key];
            });
            callback(result);
        } else {
            callback(mockData);
        }
    },
    set: (items: any, callback?: () => void) => {
        console.log("Mock set:", items);
        callback?.();
    },
    remove: (keys: string | string[], callback?: () => void) => {
        console.log("Mock remove:", keys);
        callback?.();
    },
    clear: (callback?: () => void) => {
        console.log("Mock clear");
        callback?.();
    },
    getBytesInUse: (
        keys?: string | string[],
        callback?: (bytesInUse: number) => void
    ) => {
        callback?.(0);
    },
    setAccessLevel: (accessOptions: any, callback?: () => void) => {
        console.log("Mock setAccessLevel");
        callback?.();
    },
});

const mockChrome = {
    storage: {
        local: createStorageArea(),
        onChanged: {
            addListener: (callback: any) => {},
            removeListener: (callback: any) => {},
            hasListener: (callback: any) => false,
        },
        AccessLevel: {
            TRUSTED_CONTEXTS: "TRUSTED_CONTEXTS",
            TRUSTED_AND_UNTRUSTED_CONTEXTS: "TRUSTED_AND_UNTRUSTED_CONTEXTS",
        },
    },
    runtime: {
        lastError: null,
    },
};

// Add to global
global.chrome = mockChrome as any;
