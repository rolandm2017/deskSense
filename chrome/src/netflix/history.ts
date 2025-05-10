// history.ts

class MissingComponentError extends Error {
    constructor(
        message = "The expected component was missing:",
        component: string
    ) {
        super(message + component);
        this.name = "MissingComponentError";
    }
}

export interface WatchEntry {
    showName: string;
    videoId: string;
    url: string;
    timestamp: string; // new Date().isoString()
    watchCount: number; // count of times it was watched
}

export interface DayHistory {
    [date: string]: WatchEntry[];
}

export interface WatchHistory {
    [date: string]: WatchEntry[];
}

class WatchHistoryTracker {
    history: WatchHistory;
    constructor() {
        this.history = {};
        this.loadHistory();
        this.setupEventListeners();
    }

    // Load history from Chrome storage
    async loadHistory() {
        return new Promise((resolve) => {
            chrome.storage.local.get(["watchHistory"], (result) => {
                this.history = result.watchHistory || {};
                console.log("Loaded history:", this.history);
                resolve(this.history);
            });
        });
    }

    // Save history to Chrome storage
    async saveHistory(): Promise<void> {
        return new Promise((resolve) => {
            chrome.storage.local.set({ watchHistory: this.history }, () => {
                console.log("History saved");
                resolve();
            });
        });
    }

    // Get today's date in YYYY-MM-DD format
    getTodayDate() {
        return new Date().toISOString().split("T")[0];
    }

    // Add a new watch entry
    async addWatchEntry(showName: string, videoId: string, url: string) {
        const today = this.getTodayDate();

        // Initialize today's array if it doesn't exist
        if (!this.history[today]) {
            this.history[today] = [];
        }

        // Check if this video ID already exists for today
        const existingEntry = this.history[today].find(
            (entry: WatchEntry) => entry.videoId === videoId
        );

        if (!existingEntry) {
            // Add new entry
            this.history[today].push({
                showName: showName,
                videoId: videoId,
                url: url,
                timestamp: new Date().toISOString(),
                watchCount: 1,
            });

            // Keep only last 10 days of active data
            await this.cleanupOldHistory();
            await this.saveHistory();
        }
    }

    // Remove entries older than 10 active days
    async cleanupOldHistory() {
        const dates = Object.keys(this.history).sort().reverse();

        // Keep only the most recent 10 active days
        if (dates.length > 10) {
            const daysToKeep = dates.slice(0, 10);
            const newHistory: WatchHistory = {};

            daysToKeep.forEach((date: string) => {
                newHistory[date] = this.history[date];
            });

            this.history = newHistory;
        }
    }

    // Get the most recently watched show
    getLastWatchedShow() {
        const dates = Object.keys(this.history).sort().reverse();

        for (const date of dates) {
            if (this.history[date] && this.history[date].length > 0) {
                return this.history[date][this.history[date].length - 1]
                    .showName;
            }
        }

        return null;
    }

    // Get most frequently watched show in last 3 active days
    getMostWatchedShowLastThreeDays() {
        const dates = Object.keys(this.history).sort().reverse();
        const threeDaysData = dates.slice(0, 3);
        const showCounts: Record<string, number> = {};

        threeDaysData.forEach((date) => {
            if (this.history[date]) {
                this.history[date].forEach((entry: WatchEntry) => {
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

        Object.values(this.history).forEach((dayData: WatchEntry[]) => {
            dayData.forEach((entry: WatchEntry) => {
                shows.add(entry.showName);
            });
        });

        return Array.from(shows).sort();
    }

    // Setup event listeners for the popup
    setupEventListeners() {
        // When popup opens
        document.addEventListener("DOMContentLoaded", async () => {
            await this.loadHistory();
            this.populateModal();
        });

        // Save button click
        const confirmBtn = document.getElementById("confirm-btn");
        const showSelector = document.getElementById(
            "series-select"
        ) as HTMLSelectElement;

        if (!confirmBtn) {
            throw new MissingComponentError(
                "Couldn't get modal button",
                "Modal"
            );
        }
        if (!showSelector) {
            throw new MissingComponentError(
                "Couldn't get show selector",
                "Show Selector"
            );
        }

        confirmBtn.addEventListener("click", async () => {
            const showName = showSelector.value.trim();

            if (showName) {
                // Get current tab URL
                chrome.tabs.query(
                    { active: true, currentWindow: true },
                    async (tabs) => {
                        const currentTab = tabs[0];
                        if (!currentTab.url) {
                            throw new Error("Couldn't get URL");
                        }
                        const watchMatch = currentTab.url.match(
                            /netflix\.com\/watch\/(\d+)/
                        );

                        if (watchMatch) {
                            const videoId = watchMatch[1];
                            await this.addWatchEntry(
                                showName,
                                videoId,
                                currentTab.url
                            );
                            window.close(); // Close popup after saving
                        }
                    }
                );
            }
        });

        // Toggle between dropdown and input
        const customShowInput = document.getElementById("useCustomInput");

        if (!customShowInput) {
            throw new MissingComponentError(
                "Couldn't get show text input",
                "Text input"
            );
        }
        customShowInput.addEventListener("change", (e: Event) => {
            const target = e.target as HTMLInputElement;

            const dropdown = document.getElementById("showDropdown");
            const input = document.getElementById("showInput");

            if (target.checked) {
                dropdown!.style.display = "none";
                input!.style.display = "block";
                input!.focus();
            } else {
                dropdown!.style.display = "block";
                input!.style.display = "none";
            }
        });
    }

    // Populate the modal with default values
    async populateModal() {
        await this.loadHistory();

        // Get the best default show (most recent or most watched in last 3 days)
        const lastWatched = this.getLastWatchedShow();
        const mostWatched = this.getMostWatchedShowLastThreeDays();
        const defaultShow = lastWatched || mostWatched;

        // Get all shows for dropdown
        const allShows = this.getAllShows();

        // Populate dropdown
        const dropdown = document.getElementById("showDropdown");
        if (!dropdown)
            throw new MissingComponentError(
                "Couldn't get dropdown",
                "Dropdown"
            );
        dropdown.innerHTML = "";

        // Add default option if we have one
        if (defaultShow) {
            const defaultOption = document.createElement("option");
            defaultOption.value = defaultShow;
            defaultOption.textContent = `${defaultShow} (Last watched)`;
            defaultOption.selected = true;
            dropdown.appendChild(defaultOption);
        }

        // Add all other shows
        allShows.forEach((show) => {
            if (show !== defaultShow) {
                const option = document.createElement("option");
                option.value = show;
                option.textContent = show;
                dropdown.appendChild(option);
            }
        });

        // Set up the input field with the default value
        const input = document.getElementById("showInput");
        if (defaultShow) {
            input.value = defaultShow;
        }

        // Sync dropdown and input
        dropdown.addEventListener("change", () => {
            input.value = dropdown.value;
        });
    }
}

// Initialize the tracker when popup loads
const tracker = new WatchHistoryTracker();
