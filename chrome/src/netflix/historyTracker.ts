// history.ts

import { StorageInterface } from "./storageApi";

import NetflixFacade from "./commonCodeFacade";

export interface WatchEntry {
    serverId: number; //
    urlId: string;
    showName: string;
    url: string;
    timestamp: string; // new Date().isoString()
    msTimestamp: number; // generated automatically (by the code)
    watchCount: number; // count of times it was watched
}

export class WatchHistoryTracker {
    /*
        If you're tempted to add an edit feature, remember that
        a well made top five priority algorithm will quickly derank 
        a recently added entry that does not get used.

        The user realizes their mistake, adds in the corrected version,
        selects it, and goes on with their day. The mistake vanishes in a few hours.
    */
    allHistory: WatchEntry[];
    storageConnection: StorageInterface;
    facade: NetflixFacade;

    constructor(storageConnection: StorageInterface) {
        this.storageConnection = storageConnection;
        this.allHistory = [];
        this.loadHistory();
        this.facade = new NetflixFacade();
        // this.setupEventListeners();
    }

    recordEnteredMediaTitle(title: string, url: string) {
        let urlId = url.split("/watch/")[1];
        console.log(urlId, url);
        if (urlId.includes("?")) {
            urlId = urlId.split("?")[0];
        }
        console.log("[tracker - recording]", title);
        this.addWatchEntry(urlId, title, url);
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

    // Get the most recently watched show
    getLastWatchedShow() {
        const dates = Object.keys(this.allHistory).sort().reverse();

        if (this.allHistory && this.allHistory.length > 0) {
            return this.allHistory[this.allHistory.length - 1].showName;
        }

        return null;
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

    // Remove entries older than 15 active days

    async cleanupOldHistory() {
        // Keep the past 15 days of history, and
        // at least 100 entries.
        // TODO: Get just the dates, as a Set()
        const sortedHistory: WatchEntry[] = this.allHistory.sort().reverse();

        const countOfEntries = sortedHistory.length;
        const countAbove100 =
            countOfEntries > 100 ? countOfEntries - 100 : null;

        if (countAbove100 === null) {
            return;
        }

        // Keep only the most recent 15 active days
        function getRecentEntries(entries: WatchEntry[], maxDaysAgo = 15) {
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
