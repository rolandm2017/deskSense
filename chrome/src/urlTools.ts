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

export function startsWithProtocol(s: string) {
    return s.startsWith("http://") || s.startsWith("https://");
}

export function removeProtocol(s: string) {
    if (s.startsWith("http://")) {
        return s.slice(6);
    } else if (s.startsWith("https://")) {
        return s.slice(7);
    } else {
        return s;
    }
}

export function startsWithWww(s: string) {
    return s.startsWith("www");
}

export function removeWww(s: string) {
    return s.slice(4);
}

export function hasPath(s: string) {
    // assumes protocol was removed
    return s.includes("/");
}

export function getPartBeforePath(s: string) {
    // assumes s is a url with a path and no protocol
    return s.split("/")[0];
}

export function isNormalizedFormatWithSubdomain(s: string) {
    if (s.includes("/")) {
        return false; // Can't be normalized if the protocol or path are on it
    }
    const pieces = s.split(".");

    const invalidInput = pieces.length != 3;
    if (invalidInput) {
        return false; // A normalized subdomain URL would have two .'s
    }

    return true;
}

export function startsWithSubdomain(s: string) {
    // Test assumes inputs are actual domains with a subdomain.
    // If you feed it "google.com" it won't work, it'll be a false positive
    if (s.includes("/")) {
        throw new Error("Expecting a removed protocol, and no path");
    }
    const pieces = s.split(".");

    const invalidInput = pieces.length != 3;
    if (invalidInput) {
        throw new Error("Expected subdomain dot domain dot TLD");
    }
    const subdomainAndDomainRegex =
        /^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/;

    return pieces[0].match(subdomainAndDomainRegex);
}

export function removeSubdomain(s: string) {
    console.log("Removing subdomain", s);
    const pieces = s.split(".");
    const output = pieces[1] + "." + pieces[2];
    return output;
}

// export function normalizeUrl

export function getBaseDomain(hostname: string) {
    // Function is a replacement for PSL.
    // www case is standard
    const atypicalDomainFormat = hostname.includes("www");
    if (atypicalDomainFormat) {
        const hasProtocol = hostname.slice(0, 4) === "http";
        if (hasProtocol) {
            const subdomainAndDomainEtc = hostname.split("://")[1];
            const pathIsPresent = subdomainAndDomainEtc.includes("/");
            if (pathIsPresent) {
                console.log(subdomainAndDomainEtc, "127ru");
                const relevantPart = subdomainAndDomainEtc.split("/", 1)[0];
                console.log(relevantPart, "124ru");
                if (startsWithWww(relevantPart)) {
                    const normalizedInput = removeWww(relevantPart);
                    return normalizedInput;
                }

                return relevantPart;
            }
        }
    }
    console.log(hostname, "128ru");

    const normalizedUrl = normalizeUrl(hostname);
    console.log(normalizedUrl, "180ru");
    if (
        isNormalizedFormatWithSubdomain(normalizedUrl) &&
        startsWithSubdomain(normalizedUrl)
    ) {
        return removeSubdomain(normalizedUrl);
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
        // return parts.slice(-3).join(".");
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
