// urlTools.ts

// import psl from "psl"

/*
 * Case 1:
 *  youtube.com
 *
 * Case 2:
 *  www.youtube.com
 *
 * Case 3:
 * https://www.youtube.com
 */

export function getDomainFromUrl(urlString: string) {
    try {
        const url = new URL(urlString);
        return url.hostname;
    } catch (e) {
        console.error("Invalid URL:", urlString);
        return null;
    }
}

export function removeBeforeWww(url: string) {
    /**
     * Removes everything before 'www' in a URL.
     *
     * @param {string} url - The URL to process
     * @returns {string} - The URL with everything before 'www' removed
     */
    if (url.includes("www")) {
        const index = url.indexOf("www");
        return url.substring(index);
    } else {
        return url; // Return original if 'www' not found
    }
}

export function stripProtocol(rawUrl: string) {
    if (rawUrl.startsWith("http://")) {
        const x = "http://".length;
        return rawUrl.slice(x);
    } else if (rawUrl.startsWith("https://")) {
        const x = "https://".length;
        return rawUrl.slice(x);
    }
    console.error("Unheard of protocol found", rawUrl);
}

export function urlHasProtocol(rawUrl: string) {
    return rawUrl.startsWith("http://") || rawUrl.startsWith("https://");
}

export function normalizeUrl(rawUrl: string) {
    try {
        if (!rawUrl.startsWith("http://") && !rawUrl.startsWith("https://")) {
            rawUrl = "http://" + rawUrl;
        }
        const url = new URL(rawUrl);
        let host = url.hostname.toLowerCase();
        if (host.startsWith("www.")) {
            host = host.slice(4);
        }
        return host;
    } catch (e) {
        return rawUrl.toLowerCase().replace(/^www\./, ""); // fallback
    }
}

/*
 * IF (www) -> Cut off www
 * if protocol -> cut off protocol
 *
 *
 *
 *
 */

export function getBaseDomainViaUrl(hostname: string) {
    const url = new URL(hostname);
}

export function getBaseDomain(hostname: string) {
    // www case is standard
    const atypicalDomainFormat = hostname.includes("www");
    if (atypicalDomainFormat) {
        const hasProtocol = hostname.slice(0, 4) === "http";
        if (hasProtocol) {
            const subdomainAndDomainEtc = hostname.split("://")[1];
            const pathIsPresent = subdomainAndDomainEtc.includes("/");
            if (pathIsPresent) {
                const relevantPart = subdomainAndDomainEtc.split("/", 1)[0];
                return relevantPart;
            }
        }
    }

    const parts = hostname.toLowerCase().split(".");
    if (parts.length <= 2) return hostname;
    const tlds = ["co.uk", "ac.uk", "gov.uk", "com.au", "co.jp"]; // add more if you want to be precise
    const lastTwoJoined = parts.slice(-2).join(".");
    const lastThreeJoined = parts.slice(-3).join(".");

    // remove anything after the .com:
    const pathIsPresent = parts[2].includes("/");
    if (pathIsPresent) {
        // so i.e. https://www.youtube.com/watch?v=ezPVaY-gr9I becomes
        // https://www.youtube.com
        const pathRemoved = parts[2].split("/", 1)[0];
        parts[2] = pathRemoved;
        return parts.slice(-3).join(".");
    }

    if (tlds.includes(lastTwoJoined)) {
        return parts.slice(-3).join(".");
    }
    return lastTwoJoined;
}

export function shouldBeIgnored(url: string, ignoreList: string[]) {
    // remove protocol from everything
    // because it's simpler
    if (!urlHasProtocol(url)) {
        url = "https://" + url;
    }
    const inputDomain = getBaseDomain(new URL(url).hostname);

    return ignoreList.some((ignoredDomain) => {
        const domainWithProtocol = urlHasProtocol(ignoredDomain)
            ? ignoredDomain
            : "https://" + ignoredDomain;
        try {
            const ignoredDomain = getBaseDomain(
                new URL(domainWithProtocol).hostname
            );
            return inputDomain === ignoredDomain;
        } catch {
            // If it's not a full URL, treat it as a plain domain
            return inputDomain === domainWithProtocol;
        }
    });
}
