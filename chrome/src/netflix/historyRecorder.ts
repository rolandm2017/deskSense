// historyRecorder.ts

import { StorageInterface } from "./storageApi";

import { WatchEntry } from "../interface/interfaces";

import { NetflixViewing, ViewingTracker } from "../videoCommon/visits";

import { systemInputCapture } from "../inputLogger/systemInputLogger";

// TODO: Rename to HistoryRecorder. One less "tracker" naming conflict
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
    viewingTracker: ViewingTracker;
    // facade: NetflixFacade;

    constructor(
        viewingTracker: ViewingTracker,
        storageConnection: StorageInterface
    ) {
        this.storageConnection = storageConnection;
        this.allHistory = [];
        this.loadHistory();
        this.viewingTracker = viewingTracker;
        // this.facade = new NetflixFacade();
        // this.setupEventListeners();
    }

    makeUrlId(url: string) {
        let urlId = url.split("/watch/")[1];
        if (urlId.includes("?")) {
            urlId = urlId.split("?")[0];
        }
        return urlId;
    }

    sendPageDetailsToViewingTracker(url: string) {
        systemInputCapture.capture({
            type: "NETFLIX_PAGE_LOADED",
            data: { url: url, watchPageId: this.makeUrlId(url) },
            metadata: {
                source: "sendPageDetailsToViewingTracker",
                method: "event_listener",
                location: "historyRecorder.ts",
                timestamp: Date.now(),
            },
        });
        const watchPageId = this.makeUrlId(url);
        console.log("Sending watch page ID", watchPageId);
        this.viewingTracker.reportNetflixWatchPage(watchPageId);
    }

    recordEnteredMediaTitle(title: string, url: string) {
        systemInputCapture.capture({
            type: "CHOOSE_NETFLIX_MEDIA",
            data: { title, url },
            metadata: {
                source: "recordEnteredMediaTitle",
                method: "user_input",
                location: "historyRecorder.ts",
                timestamp: Date.now(),
            },
        });
        console.log("In recordEnteredMedia");
        let urlId = this.makeUrlId(url);
        console.log("[tracker - recording]", title);
        const latestEntryUpdate: WatchEntry = this.addWatchEntry(
            urlId,
            title,
            url
        );
        console.log(latestEntryUpdate, "entry to update 49ru");
        const viewingToTrack: NetflixViewing =
            this.formatWatchEntryAsViewing(latestEntryUpdate);
        // NOTE that play/pause occurs thru background.ts in "onMessage"
        this.viewingTracker.setCurrent(viewingToTrack);
        this.saveHistory();
    }

    // Add a new watch entry
    addWatchEntry(urlId: string, showName: string, url: string) {
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

    formatWatchEntryAsViewing(entry: WatchEntry): NetflixViewing {
        const viewing = new NetflixViewing(entry);
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

    async getTopFive(): Promise<string[]> {
        // this.cleanupOldHistory();
        console.log("In getTopFive", this.allHistory.length);
        const topFiveStrings = this.allHistory.map((h: WatchEntry) => {
            return h.showName;
        });

        const seen = new Set();
        const uniqueByShowName = topFiveStrings.filter((item) => {
            if (seen.has(item)) return false;
            seen.add(item);
            return true;
        });

        return new Promise((resolve) => {
            resolve(uniqueByShowName);
        });

        // return new Promise((resolve, reject) => {
        //     resolve([
        //         "Hilda",
        //         "Lupin",
        //         "The Three Body Problem",
        //         "L'Agence",
        //         "The Invisible Guest",
        //     ]);
        // });
    }

    recordIgnoredUrl(url: string) {
        // TODO
        // systemInputCapture.capture({})
        console.log("[tracker - ignoring]", url);
    }

    // Load history from Chrome storage
    async loadHistory() {
        // TODO
        this.storageConnection
            .readWholeHistory()
            .then((entries: WatchEntry[]) => {
                console.log("Load history found: ", entries);

                this.allHistory = entries;
            });
    }

    // Save history to Chrome storage
    async saveHistory(): Promise<void> {
        // TODO
        for (const v of this.allHistory) {
            console.log("Saving ", v.showName);
        }
        this.storageConnection.saveAll(this.allHistory);
    }

    // Get today's date in YYYY-MM-DD format
    getTodaysDate() {
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
