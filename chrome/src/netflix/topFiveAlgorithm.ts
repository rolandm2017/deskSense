import { WatchEntry } from "./historyTracker";

/*

I tried 0.005 for a decay rate. It was too low!
I tried 0.02 for a decay rate. It was too high!

0.01 looks just right. 

Consider busting out a calculator if you want to adjust.

*/
const FREQUENCY_WEIGHT = 1.0;
const RECENCY_WEIGHT = 5.0;
const NOVELTY_BOOST = 50.0;
const DECAY_RATE = 0.01; // tunes how fast recency fades

export type TitleGroups = { [name: string]: WatchEntry[] };
export type Scores = { score: number; recency: number };
export type RankScores = { [name: string]: Scores };
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

    NOTE that the above brain dump was only the initial plan.
    */

    toSort: WatchEntry[];
    constructor(toSort: WatchEntry[]) {
        this.toSort = toSort;
    }

    rank(): string[] {
        // outputs five titles

        // TODO: come up with a way to recalculate the top 5 less frequently.

        const titleGroups = this.groupEntriesByTitle(this.toSort);
        const scoring: RankScores = {};

        for (const [mediaTitle, entries] of Object.entries(titleGroups)) {
            const timestamps = entries.map((entry) => entry.msTimestamp);
            const recencyScore = this.computeRecencyScore(timestamps);
            const frequencyScore = this.computeFrequencyScore(
                mediaTitle,
                this.toSort
            );

            // TODO: Cram this all in "computeNovelty" so it looks nice
            const noveltyProgress =
                this.getProgressThruNoveltyPeriodForTitle(mediaTitle);

            const noveltyScore = this.computeNovelty(noveltyProgress);

            const total = frequencyScore + recencyScore + noveltyScore;
            scoring[mediaTitle] = { score: total, recency: recencyScore };
        }

        const topFiveTitles = this.getTopFiveTitles(scoring);

        return topFiveTitles;
    }

    groupEntriesByTitle(entries: WatchEntry[]): TitleGroups {
        const groupedByTitle: TitleGroups = {};

        for (const entry of entries) {
            if (entry.showName in groupedByTitle) {
                groupedByTitle[entry.showName].push(entry);
            } else {
                groupedByTitle[entry.showName] = [entry];
            }
        }

        return groupedByTitle;
    }

    getTopFiveTitles(titleScores: RankScores): string[] {
        return Object.entries(titleScores)
            .map(([title, scores]) => ({ title, ...scores }))
            .sort((a, b) => {
                const scoreDiff = b.score - a.score;
                if (scoreDiff !== 0) return scoreDiff;
                // For ties, sort by recency (higher recency first)
                return b.recency - a.recency;
            })
            .slice(0, 5)
            .map((item) => item.title);
    }

    getProgressThruNoveltyPeriodForTitle(title: string) {
        const firstSeenDate: Date = this.getFirstSeenDateFor(
            title,
            this.toSort
        );
        const hoursElapsedSinceAdded = this.hoursBetween(
            new Date(),
            firstSeenDate
        );

        const noveltyProgress = this.convertHoursSinceBeingAddedToPercentage(
            hoursElapsedSinceAdded
        );

        return noveltyProgress;
    }

    convertHoursSinceBeingAddedToPercentage(hoursSinceBeingAdded: number) {
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
            FREQUENCY_WEIGHT * this.getRawFrequencyScore(title, allHistory);
        return frequencyScore;
    }

    getRawFrequencyScore(title: string, allHistory: WatchEntry[]) {
        // the raw value is between 0 and 1
        return (
            this.countOccurrencesInHistory(title, allHistory) /
            allHistory.length
        );
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
