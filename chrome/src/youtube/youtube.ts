// youtube.ts
import { ChannelPageOnlyError } from "../errors";
import { getDomainFromUrl, stripProtocol } from "../urlTools";
import { YouTubeViewing, viewingTracker } from "../videoCommon/visits";
import { extractChannelInfoFromWatchPage } from "./channelExtractor";

import { initializedServerApi } from "../api";

import { MissingUrlError } from "../errors";

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
    tabsWithIntervalsRecorder: Function
) {
    if (!tab.url || !tab.id || !tab.title) {
        throw new Error("Missing required tab properties");
    }

    if (isWatchingVideo(tab.url)) {
        // YouTube does lots and lots of client side rendering, so
        // a short delay ensures that the page has fully loaded
        // Use executeScript to access the DOM on YouTube watch pages
        const tabId = tab.id;
        tabsWithIntervalsRecorder(tabId);
        runningExtractChannelInfoScript = true;
        setTimeout(() => {
            chrome.scripting.executeScript(
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
                    console.log(
                        "Detected ",
                        channelName,
                        " In new page",
                        tabTitle
                    );
                    const youTubeVisit = new YouTubeViewing(
                        videoId,
                        tab.url,
                        tabTitle,
                        channelName
                    );

                    viewingTracker.setCurrent(youTubeVisit);
                    viewingTracker.reportYouTubeWatchPage();
                }
            );
            // NOTE: ** do not change this 1500 ms delay **
            // was 1500 but tha'ts too short
        }, 2900); // 1.5 second delay. The absolute minimum value.
        // 1.0 sec delay still had the "prior channel reported as current" problem
    } else if (isOnSomeChannel(tab.url)) {
        // For channel pages, we can extract from the URL
        const channelName = extractChannelNameFromUrl(tab.url);

        initializedServerApi.reportTabSwitch(
            tab.url,
            channelName ? channelName : "No channel name found"
        );
    } else if (watchingShorts(tab.url)) {
        // Avoids trying to extract the channel name from
        // the YouTube Shorts page. The page's HTML changes often. Sisyphean task.
        const domain = getDomainFromUrl(tab.url);
        // Just generic YouTube Shorts page
        initializedServerApi.reportTabSwitch(
            domain ?? "www.youtube.com/shorts",
            tab.title ? tab.title : "No title found"
        );
    } else {
        // Just generic YouTube page
        const domain = getDomainFromUrl(tab.url);

        initializedServerApi.reportTabSwitch(
            domain ?? "www.youtube.com",
            tab.title ? tab.title : "YouTube Home"
        );
    }
}

export function startSecondaryChannelExtractionScript(
    sender: chrome.runtime.MessageSender
) {
    if (!sender.tab) {
        // unhandled problem
        return;
    }
    if (runningExtractChannelInfoScript) {
        // just wait for it; it'll do al this stuff too
        return;
    }
    // TODO: Clean this up
    const tab = sender.tab;
    const tabUrl = tab.url;
    if (!tab.url) {
        throw new MissingUrlError();
    }
    const tabTitle = tab.title || "Unknown Title";
    // const channelName = getChannelNameFromSomewhere();

    // Extract video ID from URL
    let videoId = getYouTubeVideoId(tabUrl);

    // TODO: Get channel name from somewhere
    const youTubeVisit = new YouTubeViewing(
        videoId,
        tab.url,
        tabTitle,
        "Unknown Channel"
    );
    // youTubeVisit.sendInitialInfoToServer();

    viewingTracker.setCurrent(youTubeVisit);
}

export function getYouTubeChannel(youTubeUrl: string) {
    // try this way first
    if (isWatchingVideo(youTubeUrl)) {
        return extractChannelInfoFromWatchPage();
    } else if (isOnSomeChannel(youTubeUrl)) {
        return extractChannelNameFromUrl(youTubeUrl);
    } else {
        console.log("Cannot get channel name from ", youTubeUrl);
        return null;
    }
}

export function isWatchingVideo(youTubeUrl: string) {
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
        console.error("Error in splitYouTubeUrlFromVideoId");
        console.log(url);
        console.log(e);
        return "Unknown ID";
    }
}

export function getYouTubeVideoId(url: string | undefined) {
    console.log(url, "192ru");
    let videoId;
    if (url) {
        videoId = splitYouTubeUrlFromVideoId(url);
    } else {
        videoId = "Missing URL";
        throw new MissingUrlError();
    }
    return videoId;
}
