// youtube.ts
import { ChannelPageOnlyError } from "../errors";
import { getDomainFromUrl, stripProtocol } from "../urlTools";
import {
    viewingTracker,
    ViewingTracker,
    YouTubeViewing,
} from "../videoCommon/visits";
import { extractChannelInfoFromWatchPage } from "./channelExtractor";

import { taskTypes } from "../const";
import { getDependencies } from "../dependencies";
import { MissingUrlError } from "../errors";
import { Task } from "../interface/interfaces";

/*
 * For YouTube, some channels are productive; others are not.
 *
 * User must be able to tag which channel is which.
 *
 * The extension must be able to tell which channel is active.
 */

let runningExtractChannelInfoScript = false;

// // Handle YouTube URL specifically
export function handleYouTubeUrl(
    tab: chrome.tabs.Tab,
    onAsyncTask?: (task: Task) => void,
    tracker: ViewingTracker = viewingTracker
): Task | undefined {
    if (!tab.url || !tab.id || !tab.title) {
        throw new Error("Missing required tab properties");
    }

    const { chromeApi, scrapeDelay } = getDependencies();

    if (isWatchingYouTubeVideo(tab.url)) {
        // YouTube does lots and lots of client side rendering, so
        // a short delay ensures that the page has fully loaded
        // Use executeScript to access the DOM on YouTube watch pages
        const tabId = tab.id;
        // TODO: IF tab ID in cache, use that!
        let foundCachedState = false;
        if (tracker.hasPlayerStateForTab(tabId)) {
            foundCachedState = true;
            const youTubeState = tracker.useStoredPlayerState(tabId);
            console.log("Returning cached YouTube state for tab", tabId);
            if (youTubeState instanceof YouTubeViewing) {
                return {
                    type: taskTypes.YOUTUBE_WATCH_PAGE_RETURN,
                    data: youTubeState,
                };
            }
            console.warn("Found Netflix Viewing where a YouTube was expected");
            // fallback to scraping it again
        }
        // console.log("Running script for ", tab.title);
        runningExtractChannelInfoScript = true;
        // Always use setTimeout to make it consistently async

        setTimeout(() => {
            chromeApi.executeScript(
                {
                    target: { tabId: tabId },
                    func: extractChannelInfoFromWatchPage,
                },
                (results) => {
                    const tabTitle = tab.title ? tab.title : "Unknown Title";

                    if (tab.url === undefined) {
                        throw new MissingUrlError();
                    }

                    let videoId = getYouTubeVideoId(tab.url);

                    let channelName = "Unknown Channel";
                    if (results && results[0] && results[0].result) {
                        // TODO: Get the video player info
                        channelName = results[0].result;
                    }

                    // FIXME: Need to get Player State for tabs into it
                    // tabbing into youtube watch page with player going -> "paused"
                    console.log(
                        "Detected: ",
                        channelName,
                        " In new page:",
                        tabTitle
                    );
                    const youTubeVisit = new YouTubeViewing(
                        videoId,
                        tab.url,
                        tabTitle,
                        channelName,
                        tabId
                    );

                    if (onAsyncTask) {
                        onAsyncTask({
                            type: taskTypes.YOUTUBE_WATCH_PAGE,
                            data: youTubeVisit,
                        }); // Callback handles the async result
                    }
                    return;
                }
            );
            // NOTE: ** do not change this 1500 ms delay **
            // was 1500 but tha'ts too short
        }, scrapeDelay); // 1.5 second delay. The absolute minimum value.
        // 1.0 sec delay still had the "prior channel reported as current" problem
        return undefined;
    } else if (isOnSomeChannel(tab.url)) {
        // For channel pages, we can extract from the URL
        const channelName = extractChannelNameFromUrl(tab.url);

        return { type: taskTypes.YOUTUBE_CHANNEL_PAGE, data: { channelName } };
    } else if (watchingShorts(tab.url)) {
        // Avoids trying to extract the channel name from
        // the YouTube Shorts page. The page's HTML changes often. Sisyphean task.
        const domain = getDomainFromUrl(tab.url);
        // Just generic YouTube Shorts page
        return {
            type: taskTypes.YOUTUBE_SHORTS,
            data: {
                domain: domain ?? "www.youtube.com/shorts",
                tabTitle: tab.title ? tab.title : "No title found",
            },
        };
    } else {
        // Just generic YouTube page
        const domain = getDomainFromUrl(tab.url);

        return {
            type: taskTypes.YOUTUBE_HOME,
            data: {
                domain: domain ?? "www.youtube.com",
                tabTitle: tab.title ? tab.title : "YouTube Home",
            },
        };
    }
}

export function getYouTubeChannel(youTubeUrl: string) {
    // try this way first
    if (isWatchingYouTubeVideo(youTubeUrl)) {
        return extractChannelInfoFromWatchPage();
    } else if (isOnSomeChannel(youTubeUrl)) {
        return extractChannelNameFromUrl(youTubeUrl);
    } else {
        console.log("Cannot get channel name from ", youTubeUrl);
        return null;
    }
}

export function isWatchingYouTubeVideo(youTubeUrl: string) {
    return youTubeUrl.includes("youtube.com/watch");
}

export function isOnSomeChannel(youTubeUrl: string) {
    return youTubeUrl.includes("@");
}

export function watchingShorts(youTubeUrl: string) {
    return youTubeUrl.includes("www.youtube.com/shorts/");
}

export function extractChannelNameFromUrl(youTubeUrl: string) {
    const onSomeChannelsPage = youTubeUrl.includes("@");
    if (onSomeChannelsPage) {
        // Examples of valid URLs for this func:
        // https://www.youtube.com/@pieceoffrench
        // https://www.youtube.com/@pieceoffrench/featured
        // https://www.youtube.com/@pieceoffrench/videos
        // https://www.youtube.com/@pieceoffrench/streams
        const hasProtocol = youTubeUrl.startsWith("http");
        if (hasProtocol) {
            const withoutProtocol = stripProtocol(youTubeUrl);
            if (withoutProtocol === undefined) {
                throw new Error("URL did not have a protocol");
            }
            const segments = withoutProtocol?.split("/");
            return segments[1].slice(1);
        } else {
            const segments = youTubeUrl.split("/");
            return segments[1].slice(1);
        }
    }
    throw new ChannelPageOnlyError("Was not on a channel page");
}

function splitYouTubeUrlFromVideoId(url: string) {
    // TODO: Put some examples here
    try {
        let videoId = url.split("v=")[1]; // Extract video ID
        // console.log("VIDEO ID: ", videoId, videoId.includes("&t"));
        if (videoId.includes("&t")) {
            videoId = videoId.split("&")[0];
            // console.log("And NOW it is: ", videoId);
        }
        return videoId;
    } catch (e) {
        console.error("Error in splitYouTubeUrlFromVideoId", url);
        return "Unknown ID";
    }
}

export function getYouTubeVideoId(url: string | undefined) {
    let videoId;
    if (url) {
        videoId = splitYouTubeUrlFromVideoId(url);
    } else {
        videoId = "Missing URL";
        throw new MissingUrlError();
    }
    return videoId;
}
