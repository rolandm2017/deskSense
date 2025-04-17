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

export function removeBeforeWww(url) {
    /**
     * Removes everything before 'www' in a URL.
     *
     * @param {string} url - The URL to process
     * @returns {string} - The URL with everything before 'www' removed
     */
    if (url.includes("www")) {
        const index = url.indexOf("www")
        return url.substring(index)
    } else {
        return url // Return original if 'www' not found
    }
}

export function stripProtocol(rawUrl) {
    if (rawUrl.startsWith("http://")) {
        const x = "http://".length
        return rawUrl.slice(x)
    } else if (rawUrl.startsWith("https://")) {
        const x = "https://".length
        return rawUrl.slice(x)
    }
    console.error("Unheard of protocol found", rawUrl)
}

export function normalizeUrl(rawUrl) {
    try {
        if (!rawUrl.startsWith("http://") && !rawUrl.startsWith("https://")) {
            rawUrl = "http://" + rawUrl
        }
        const url = new URL(rawUrl)
        let host = url.hostname.toLowerCase()
        if (host.startsWith("www.")) {
            host = host.slice(4)
        }
        return host
    } catch (e) {
        return rawUrl.toLowerCase().replace(/^www\./, "") // fallback
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
