/*

* Feature is intended to enable user to ignore tracking of any domain they choose.

*/

class IgnoredDomains {
    /* Was previously just a string array in a let, but
     * moving it to its own file necessitated an object to be strict */
    ignoreList: string[];
    constructor(list: string[]) {
        this.ignoreList = list;
    }

    addNew(entry: string) {
        this.ignoreList.push(entry);
    }

    fromStorage(entries: string[]) {
        this.ignoreList = entries;
    }

    getAll() {
        return this.ignoreList;
    }
}

// Load domains when extension starts
export let ignoredDomains: IgnoredDomains = new IgnoredDomains([]);

export function setupIgnoredDomains() {
    // Make sure the service worker is ready before setting up listeners

    // FIXME: are newly added ignored domains getting added?

    if (chrome.storage) {
        // Now it is safe to use chrome.storage
        // Listen for storage changes
        chrome.storage.onChanged.addListener((changes, area) => {
            if (area === "local" && changes.ignoredDomains) {
                console.log(
                    "Changes in ignoredDomains:",
                    changes.ignoredDomains
                );
                if (changes.ignoredDomains.newValue) {
                    ignoredDomains.addNew(changes.ignoredDomains.newValue);
                }
            }
        });
    } else {
        console.error("chrome.storage is not available!");
    }

    loadIgnoredDomains();
}

export function loadIgnoredDomains() {
    chrome.storage.local.get("ignoredDomains", (data) => {
        ignoredDomains = new IgnoredDomains(data.ignoredDomains || []);
    });
}

// Example: Check if a domain is in the ignored list
export function isDomainIgnored(domain: string, ignoreList: string[]) {
    // console.log("ignore list: ", ignoreList)
    // TODO: Make it use binary search
    return ignoreList.some(
        (ignoredDomain) =>
            domain === ignoredDomain ||
            ignoredDomain.includes(domain) ||
            domain.includes(ignoredDomain)
    );
}
