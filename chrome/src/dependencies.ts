// dependencies.ts - Centralized dependency container
// Abstract the Chrome APIs

// if you ask why this is here at all, think: testing!

export interface ChromeApi {
    executeScript: (
        options: chrome.scripting.ScriptInjection<any[], any>,
        callback: (results: chrome.scripting.InjectionResult[]) => void
    ) => void;
}

export const regularExecuteScript: ChromeApi = {
    executeScript: (options, callback) =>
        chrome.scripting.executeScript(options, callback),
};

export interface Dependencies {
    chromeApi: ChromeApi;
    scrapeDelay: number;
}

// Default production dependencies
export const regularDependencies: Dependencies = {
    chromeApi: regularExecuteScript,
    scrapeDelay: 2900,
};

// Global dependencies (can be overridden for testing)
let currentDependencies: Dependencies = regularDependencies;

export function setDependencies(deps: Partial<Dependencies>) {
    currentDependencies = { ...currentDependencies, ...deps };
}

export function getDependencies(): Dependencies {
    // Outside of the testing environment, this replaces
    // chrome.scripting.executeScript
    // with chromeApi.executeScript
    return currentDependencies;
}

export function resetDependencies() {
    currentDependencies = regularDependencies;
}
