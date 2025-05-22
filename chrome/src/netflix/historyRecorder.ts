// netflix/historyRecorder.ts

import { StorageInterface } from "./storageApi";

import { WatchEntry } from "../interface/interfaces";

import { NetflixViewingSansState } from "../videoCommon/visits";

import { makeNetflixWatchPageId } from "./netflixUrlTool";
import { TopFiveAlgorithm } from "./topFiveAlgorithm";

export class MessageRelay {
    constructor() {
        //
    }

    // NOTE that play/pause occurs thru background.ts in "onMessage"
    alertTrackerOfNetflixMediaInfo(viewingToTrack: NetflixViewingSansState) {
        chrome.runtime.sendMessage({
            event: "netflix_media_selected",
            media: {
                url: viewingToTrack.url,
                videoId: viewingToTrack.videoId,
                mediaTitle: viewingToTrack.mediaTitle,
            },
        });
    }

    alertTrackerOfNetflixPage(fullUrl: string, pageId: string) {
        chrome.runtime.sendMessage({
            event: "netflix_page_opened",
            media: {
                fullUrl: fullUrl,
                pageId: pageId,
            },
        });
    }
}

export class HistoryRecorder {
    /*
        If you're tempted to add an edit feature, remember that
        a well made top five priority algorithm will quickly derank 
        a recently added entry that does not get used.

        The user realizes their mistake, adds in the corrected version,
        selects it, and goes on with their day. The mistake vanishes in a few hours.
    */
    allHistory: WatchEntry[];
    storageConnection: StorageInterface;
    relay: MessageRelay;
    dbLoaded: Promise<void>;

    // facade: NetflixFacade;

    constructor(
        storageConnection: StorageInterface,
        backgroundScriptRelay: MessageRelay
    ) {
        this.storageConnection = storageConnection;
        this.allHistory = [];
        this.relay = backgroundScriptRelay;
        this.dbLoaded = this.loadHistory();
    }

    static async create(
        storageConnection: StorageInterface,
        backgroundScriptRelay: MessageRelay
    ): Promise<HistoryRecorder> {
        // Use this to make new HistoryRecorders.
        // const recorder = await HistoryRecorder.create(storageConnection, relay);
        const instance = new HistoryRecorder(
            storageConnection,
            backgroundScriptRelay
        );
        await instance.loadHistory();
        return instance;
    }

    sendPageDetailsToViewingTracker(url: string) {
        const watchPageId = makeNetflixWatchPageId(url);
        console.log("Sending watch page ID", watchPageId);
        this.relay.alertTrackerOfNetflixPage(url, watchPageId);
    }

    recordEnteredMediaTitle(
        title: string,
        url: string,
        playerState: "playing" | "paused"
    ) {
        console.log("In recordEnteredMedia");
        let watchPageId = makeNetflixWatchPageId(url);
        console.log("[tracker - recording]", title);
        const latestEntryUpdate: WatchEntry = this.addWatchEntry(
            watchPageId,
            title,
            url
        );
        const viewingToTrack: NetflixViewingSansState =
            this.formatWatchEntryAsViewing(latestEntryUpdate);
        // NOTE that play/pause occurs thru background.ts in "onMessage"
        this.relay.alertTrackerOfNetflixMediaInfo(viewingToTrack);
        this.saveHistory();
    }

    // Add a new watch entry
    addWatchEntry(urlId: string, showName: string, url: string) {
        // This function is NOT an entrypoint into the class!
        if (!this.validateUrlId(urlId)) {
            console.warn("Received invalid URL ID: ", urlId);
        }

        const newEntry: WatchEntry = {
            serverId: 1000, // temp
            urlId: urlId, // still use the string anyway, valid or not
            showName: showName,
            url: url,
            timestamp: new Date().toISOString(),
            msTimestamp: Date.now(), // number of ms since Jan 1, 1970
            watchCount: 1,
        };
        this.allHistory.push(newEntry);
        return newEntry;
    }
    // so, i pick hilda, i watch hilda, i pick hilda again.
    // does hilda now have two watchEntries in the history?
    // I guess it does. repeat all the data? yes for now

    validateUrlId(urlId: string) {
        // checks that it is just a bunch of numbers.
        // "234032" passes but "234o32" fails
        const isNumeric = /^\d+$/.test(urlId);
        return isNumeric;
    }

    formatWatchEntryAsViewing(entry: WatchEntry): NetflixViewingSansState {
        const viewing = new NetflixViewingSansState(
            entry.urlId,
            entry.showName,
            entry.url
        );
        return viewing;
    }

    /*  Why there is no recordPauseEvent, recordPlayEvent on this class:
    // 
    //      So, the facade gets to know what the user's
    // currently watched media is.
    // The facade also gets to know when they leave the page
    // so it can issue a pause cmd. Or, perhaps the server will
    // just know because the Chrome session changed.
    // Anyweay, the facade knows the current Watch page title.
    // So then, the video player state script is injected.
    // It tells the facade, "Hey it's playing" Or "Hey it's paused"
    // and behind the facade, something issues play, pause payloads
    // as needed.
    // use current state and tell the server it's paused
    // }
    */

    async loadDropdown(): Promise<string[]> {
        // TODO: Decide when and where you want to have historyCleanup performed!
        // This function is just a suggestion.
        await this.dbLoaded;
        this.cleanupOldHistory();
        return this.getTopFive();
    }

    async getTopFive(): Promise<string[]> {
        console.log("In getTopFive", this.allHistory.length);
        await this.dbLoaded;

        const topFiveAlgorithm = new TopFiveAlgorithm(this.allHistory);
        const topFiveRanked = topFiveAlgorithm.rank();

        return new Promise((resolve) => {
            resolve(topFiveRanked);
        });
    }

    recordIgnoredUrl(url: string) {
        // TODO
        console.log("[tracker - ignoring]", url);
    }

    // Load history from Chrome storage
    async loadHistory() {
        this.allHistory = await this.storageConnection.readWholeHistory();
    }

    // Save history to Chrome storage
    async saveHistory(): Promise<void> {
        // TODO
        for (const v of this.allHistory) {
            console.log("Saving ", v.showName);
        }
        this.storageConnection.saveAll(this.allHistory);
    }

    getTodaysDate() {
        // Get today's date in YYYY-MM-DD format
        return new Date().toISOString().split("T")[0];
    }

    // Get most frequently watched show in last 3 active days
    getMostWatchedShowLastThreeDays() {
        const dates = Object.keys(this.allHistory).sort().reverse();
        const threeDaysData = dates.slice(0, 3);
        const showCounts: Record<string, number> = {};

        threeDaysData.forEach((date) => {
            if (this.allHistory) {
                this.allHistory.forEach((entry: WatchEntry) => {
                    showCounts[entry.showName] =
                        (showCounts[entry.showName] || 0) + 1;
                });
            }
        });

        // Return the show with the highest count
        return (
            Object.keys(showCounts).reduce((a, b) =>
                (showCounts[a] || 0) > (showCounts[b] || 0) ? a : b
            ) || null
        );
    }

    // Get unique shows from history for dropdown
    getAllShows(): string[] {
        const shows: Set<string> = new Set();

        Object.values(this.allHistory).forEach((entry: WatchEntry) => {
            shows.add(entry.showName);
        });

        return Array.from(shows).sort();
    }

    async cleanupOldHistory() {
        // Keep the past 15 days of history, and
        // at least 100 entries.
        const maxDaysAgo = 15;
        const maxHistoryCount = 100;
        // TODO: Get just the dates, as a Set()
        const sortedHistory: WatchEntry[] = this.allHistory.sort().reverse();

        const countOfEntries = sortedHistory.length;
        const countAbove100 =
            countOfEntries > maxHistoryCount
                ? countOfEntries - maxHistoryCount
                : null;

        if (countAbove100 === null) {
            return;
        }

        // Keep only the most recent 15 active days
        function getRecentEntries(entries: WatchEntry[]) {
            const fifteenDaysAgo = new Date();
            fifteenDaysAgo.setDate(fifteenDaysAgo.getDate() - maxDaysAgo);

            return entries.filter(
                (entry: WatchEntry) =>
                    new Date(entry.timestamp) >= fifteenDaysAgo
            );
        }

        const entriesToKeep = getRecentEntries(sortedHistory);
        this.allHistory = entriesToKeep;
    }
}
