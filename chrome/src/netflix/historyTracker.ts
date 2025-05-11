// history.ts

import { StorageInterface } from "./storageApi";

export interface WatchEntry {
    videoId: string;
    showName: string;
    url: string;
    timestamp: string; // new Date().isoString()
    watchCount: number; // count of times it was watched
}

export class WatchHistoryTracker {
    pastHistory: WatchEntry[];
    todayHistory: WatchEntry[];
    storageConnection: StorageInterface;

    constructor(storageConnection: StorageInterface) {
        this.storageConnection = storageConnection;
        this.todayHistory = [];
        this.pastHistory = [];
        this.loadHistory();
        // this.setupEventListeners();
    }

    // Add a new watch entry
    async addWatchEntry(videoId: string, showName: string, url: string) {
        const today = this.getTodaysDate();

        // Check if this video ID already exists for today
        const existingEntry = this.todayHistory.find(
            (entry: WatchEntry) => entry.videoId === videoId
        );

        if (!existingEntry) {
            // Add new entry
            this.todayHistory.push({
                videoId: videoId,
                showName: showName,
                url: url,
                timestamp: new Date().toISOString(),
                watchCount: 1,
            });

            // Keep only last 10 days of active data
            await this.cleanupOldHistory();
            await this.saveHistory();
        }
    }

    async getTopFive(): Promise<string[]> {
        this.cleanupOldHistory();
        return new Promise((resolve, reject) => {
            resolve([
                "Hilda",
                "Lupin",
                "The Three Body Problem",
                "L'Agence",
                "The Invisible Guest",
            ]);
        });
    }

    recordEnteredValue(title: string) {
        console.log(title);
    }

    handleIgnoreUrl(url: string) {
        console.log(url);
    }

    // Load history from Chrome storage
    async loadHistory() {
        // TODO
        this.storageConnection.readAll().then((days) => {
            this.pastHistory = days;

            // FIXME: but how to get previous entries from today? maybe
            // go into the pastHistory and get the one for today
        });
    }

    // Save history to Chrome storage
    async saveHistory(): Promise<void> {
        // TODO
        this.storageConnection.saveDay(this.todayHistory);
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
        const pastHistoryDates = this.pastHistory.sort().reverse();

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
