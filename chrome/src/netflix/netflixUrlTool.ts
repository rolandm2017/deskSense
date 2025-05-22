export function makeNetflixWatchPageId(url: string) {
    let urlId = url.split("/watch/")[1];
    if (urlId.includes("?")) {
        urlId = urlId.split("?")[0];
    }
    return urlId;
}
