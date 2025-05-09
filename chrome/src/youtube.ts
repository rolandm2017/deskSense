// youtube.ts
import { extractChannelInfoFromWatchPage } from "./channelExtractor";
import { ChannelPageOnlyError } from "./errors";
import { stripProtocol } from "./urlTools";

/*
 * For YouTube, some channels are productive; others are not.
 *
 * User must be able to tag which channel is which.
 *
 * The extension must be able to tell which channel is active.
 */

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
