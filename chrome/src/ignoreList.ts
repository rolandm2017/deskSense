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

export function loadDomains() {
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
