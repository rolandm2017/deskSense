class TopFiveAlgorithm {
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
    constructor() {
        //
    }

    rank() {
        const sorted = [];
    }
}
