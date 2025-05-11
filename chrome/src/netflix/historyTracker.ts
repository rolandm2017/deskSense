// history.ts

import { StorageInterface } from "./storageApi";

export interface WatchEntry {
    serverId: number; //
    urlId: string;
    showName: string;
    url: string;
    timestamp: string; // new Date().isoString()
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
    todayHistory: WatchEntry[];
    storageConnection: StorageInterface;

    constructor(storageConnection: StorageInterface) {
        this.storageConnection = storageConnection;
        this.todayHistory = [];
        this.allHistory = [];
        this.loadHistory();
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
    async addWatchEntry(urlId: string, showName: string, url: string) {
        if (!this.validateUrlId(urlId)) {
            console.warn("Received invalid URL ID: ", urlId);
        }
        const today = this.getTodaysDate();

        // Check if this video ID already exists for today
        const existingEntry = this.todayHistory.find(
            (entry: WatchEntry) => entry.urlId === urlId
        );

        if (!existingEntry) {
            // Add new entry
            const newEntry: WatchEntry = {
                serverId: 1000, // temp
                urlId: urlId, // still use the string anyway, valid or not
                showName: showName,
                url: url,
                timestamp: new Date().toISOString(),
                watchCount: 1,
            };
            this.todayHistory.push(newEntry);
            this.allHistory.push(newEntry);

            // Keep only last 10 days of active data
            // await this.cleanupOldHistory();
            // await this.saveHistory();
        }
    }

    validateUrlId(urlId: string) {
        // checks that it is just a bunch of numbers.
        // "234032" passes but "234o32" fails
        const isNumeric = /^\d+$/.test(urlId);
        return isNumeric;
    }

    async getTopFive(): Promise<string[]> {
        // this.cleanupOldHistory();
        console.log("In getTopFive", this.allHistory.length);
        console.log(this.allHistory, "85ru");
        const topFiveStrings = this.allHistory.map((h: WatchEntry) => {
            console.log(h, h.showName, "87ru");
            return h.showName;
        });
        console.log(topFiveStrings, "89ru");

        return new Promise((resolve) => {
            resolve(topFiveStrings);
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
                for (const d of entries) {
                    console.log(d, "d in entries. should be watchHistory");
                }
                this.allHistory = entries;

                // FIXME: but how to get previous entries from today? maybe
                // go into the pastHistory and get the one for today
            });
    }

    // Save history to Chrome storage
    async saveHistory(): Promise<void> {
        // TODO
        this.storageConnection.saveAll(this.todayHistory);
    }

    // Get today's date in YYYY-MM-DD format
    getTodaysDate() {
        return new Date().toISOString().split("T")[0];
    }

    // Get the most recently watched show
    getLastWatchedShow() {
        const dates = Object.keys(this.todayHistory).sort().reverse();

        for (const date of dates) {
            if (this.todayHistory && this.todayHistory.length > 0) {
                return this.todayHistory[this.todayHistory.length - 1].showName;
            }
        }

        return null;
    }

    // Get most frequently watched show in last 3 active days
    getMostWatchedShowLastThreeDays() {
        const dates = Object.keys(this.todayHistory).sort().reverse();
        const threeDaysData = dates.slice(0, 3);
        const showCounts: Record<string, number> = {};

        threeDaysData.forEach((date) => {
            if (this.todayHistory) {
                this.todayHistory.forEach((entry: WatchEntry) => {
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

        Object.values(this.todayHistory).forEach((entry: WatchEntry) => {
            shows.add(entry.showName);
        });

        return Array.from(shows).sort();
    }

    // Remove entries older than 10 active days
    async cleanupOldHistory() {
        // TODO: Get just the dates, as a Set()
        const pastHistoryDates = this.allHistory.sort().reverse();

        // Keep only the most recent 10 active days
        if (pastHistoryDates.length > 10) {
            const daysToKeep = pastHistoryDates.slice(0, 9);
            const newHistory: WatchEntry[] = [];

            daysToKeep.forEach((entry: WatchEntry) => {
                // get the pastHistoryDates for the
                //
                newHistory.push();
            });

            this.todayHistory = newHistory;
        }
    }
}
