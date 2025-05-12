import { WatchEntry } from "./historyTracker";

const FREQUENCY_WEIGHT = 1.0;
const RECENCY_WEIGHT = 5.0;
const NOVELTY_BOOST = 50.0;
const DECAY_RATE = 0.01; // tunes how fast recency fades

/*

I tried 0.005 for a decay rate. It was too low!
I tried 0.02 for a decay rate. It was too high!

0.01 looks just right. 

Consider busting out a calculator if you want to adjust.

*/

export class TopFiveAlgorithm {
    /*
    
    For the purposes of this file(?), a series title and a movie title are the same.

    User is expected to categorize inputs by series title and movie title.

    Qualities of a good top five algorithm:
        - A newly entered title, that gets used for an entry, shows up as #1.
        - A newly entered title that is not being used, quickly deranks.
        - The frequency with which a title is selected, contributes to the ranking.
            • You use the title a lot, it shows up higher in the list.
        - There is a recency effect: More recently used titles are weighted higher.
            • Initial idea is an exponential decay. y = 10 * (1/2)^x. 10 at 0, 5 at 1, 2.5 at 2.
            • Followup idea is an exponential decay plus a mild offset.
    
    Recency effect algorithm:
        - Initial idea is an exponential decay. y = 10 * (1/2)^x. 10 at 0, 5 at 1, 2.5 at 2.
        - Followup idea is an exponential decay plus a mild offset.
                • So y = (10 * (1/2)^x) + 2, so values around x = 5 still get the + 2.
        - Additionally the decay of 1/2 is probably too steep. 4/5 might be better.
    */

    toSort: WatchEntry[];
    constructor(toSort: WatchEntry[]) {
        this.toSort = toSort;
    }

    rank(): string[] {
        // outputs five titles
        const topFiveTitles = [];

        // TODO: come up with a way to recalculate the top 5 less frequently.

        const startedGroups: string[] = [];
        const counts: { [name: string]: number } = {};
        const groupedByTitle: { [name: string]: WatchEntry[] } = {};

        let count = 0;

        for (const entry of this.toSort) {
            count++;
            if (entry.showName in startedGroups) {
                counts[entry.showName]++;
                groupedByTitle[entry.showName].push(entry);
            } else {
                counts[entry.showName] = 1;
                groupedByTitle[entry.showName] = [entry];

                startedGroups.push(entry.showName);
            }
        }

        for (const [mediaTitle, entries] of Object.entries(groupedByTitle)) {
            const timestamps = entries.map((entry) => entry.msTimestamp);
            const recencyScore = this.computeRecencyScore(timestamps);
            const frequencyScore = this.computeFrequencyScore(
                mediaTitle,
                this.toSort
            );

            // TODO: Cram this all in "computeNovelty" so it looks nice
            const firstSeenDate: Date = this.getFirstSeenDateFor(
                mediaTitle,
                this.toSort
            );
            const hoursElapsedSinceAdded = this.hoursBetween(
                new Date(),
                firstSeenDate
            );

            const noveltyProgress = this.getProgressThruNoveltyPeriod(
                hoursElapsedSinceAdded
            );

            const noveltyScore = this.computeNovelty(noveltyProgress);
        }

        return [];
    }

    getProgressThruNoveltyPeriod(hoursSinceBeingAdded: number) {
        const noveltyPeriodInHours = 72;
        return hoursSinceBeingAdded / noveltyPeriodInHours;
    }

    oneHourAsMilliseconds = 3600000; // (1000 * 60 * 60)

    computeRecencyScore(timestampsFromGroup: number[], now = Date.now()) {
        // timestamps: Array of Unix timestamps when the show was watched

        // decayRate: Lower = slower decay. Try 0.05 for hourly, 0.005 for daily decay
        // time-weighted frequency sum, where
        // each individual viewing gets a score that decays with time
        const rawScore = this.getRawRecencyScore(timestampsFromGroup);
        const maxPossibleScore = timestampsFromGroup.length;
        const normalizedScore = (rawScore / maxPossibleScore) * 100;
        return normalizedScore;
    }

    getRawRecencyScore(timestamps: number[], now = Date.now()) {
        return timestamps.reduce((score, ts) => {
            const hoursAgo = (now - ts) / this.oneHourAsMilliseconds;
            const decayedRating = this.exponentialDecay(hoursAgo);
            return score + decayedRating;
        }, 0);
    }

    exponentialDecay(hoursAgo: number) {
        // Returns a time-decayed weight using exponential decay, where
        // more recent events contribute more.
        // Used to prioritize recent user activity in scoring algorithms.
        return Math.exp(-DECAY_RATE * hoursAgo);
    }

    computeFrequencyScore(title: string, allHistory: WatchEntry[]) {
        const frequencyScore =
            (FREQUENCY_WEIGHT *
                this.countOccurrencesInHistory(title, allHistory)) /
            allHistory.length;
        return frequencyScore;
    }

    countOccurrencesInHistory(title: string, allHistory: WatchEntry[]) {
        let counter = 0;
        for (const entry of allHistory) {
            if (title === entry.showName) {
                counter++;
            }
        }
        return counter;
    }

    computeNovelty(percentThruNoveltyPeriod: number) {
        // Progress as in, progress towards the end of the novelty period
        const rawScore = this.getPositionOnCircle(percentThruNoveltyPeriod);
        const lessAggroLine = this.getAdjustmentWithAverage(
            rawScore,
            percentThruNoveltyPeriod
        );
        // A score will go from 1 down to 0. Unless you opt for a less aggro line.
        return rawScore;
    }

    getPositionOnCircle(x: number) {
        // top right quadrant of circle
        return Math.sqrt(1 - x ** 2); // Unit circle (r=1)
    }

    getAdjustmentWithAverage(rawScore: number, x: number) {
        return (rawScore + x) / 2;
    }

    getFirstSeenDateFor(mediaTitle: string, allHistory: WatchEntry[]): Date {
        let firstSeenDate = new Date();
        for (const entry of allHistory) {
            const timestampAsDate = new Date(entry.timestamp);
            if (timestampAsDate < firstSeenDate) {
                firstSeenDate = timestampAsDate;
            }
        }
        return firstSeenDate;
    }

    hoursBetween(date1: Date, date2: Date) {
        return Math.abs(date2.getTime() - date1.getTime()) / (1000 * 60 * 60);
    }
}
