import { WatchEntry } from "../../src/interface/interfaces";

function makeWatchEntry(
    serverId: number,
    urlId: string,
    showName: string,
    url: string,
    timestamp: string,
    watchCount: number
): WatchEntry {
    return {
        serverId,
        urlId,
        showName,
        url,
        timestamp,
        msTimestamp: new Date(timestamp).getTime(),
        watchCount,
    };
}

export const pretendPreexistingHistory: WatchEntry[] = [
    // Day 1: 1 entry

    makeWatchEntry(
        1001,
        "80019819",
        "The Queen's Gambit",
        "netflix.com/watch/80019819",
        "2025-04-24T09:15:22.431Z",
        2
    ),

    // Day 2: 7 entries
    makeWatchEntry(
        1002,
        "70264235",
        "Stranger Things",
        "netflix.com/watch/70264235",
        "2025-04-25T08:30:15.123Z",
        1
    ),
    makeWatchEntry(
        1003,
        "80192098",
        "The Crown",
        "netflix.com/watch/80192098",
        "2025-04-25T10:45:33.892Z",
        3
    ),
    makeWatchEntry(
        1004,
        "70153404",
        "House of Cards",
        "netflix.com/watch/70153404",
        "2025-04-25T14:22:11.567Z",
        1
    ),
    makeWatchEntry(
        1005,
        "70299043",
        "Orange Is the New Black",
        "netflix.com/watch/70299043",
        "2025-04-25T16:18:45.234Z",
        2
    ),
    makeWatchEntry(
        1006,
        "80199790",
        "Mindhunter",
        "netflix.com/watch/80199790",
        "2025-04-25T18:33:09.678Z",
        1
    ),
    makeWatchEntry(
        1007,
        "80175722",
        "Bird Box",
        "netflix.com/watch/80175722",
        "2025-04-25T20:15:58.901Z",
        4
    ),
    makeWatchEntry(
        1008,
        "80189221",
        "The Irishman",
        "netflix.com/watch/80189221",
        "2025-04-25T22:48:27.345Z",
        2
    ),

    // Day 3: 6 entries
    makeWatchEntry(
        1009,
        "80063637",
        "Breaking Bad",
        "netflix.com/watch/80063637",
        "2025-04-26T07:20:14.567Z",
        5
    ),
    makeWatchEntry(
        1010,
        "81041900",
        "Emily in Paris",
        "netflix.com/watch/81041900",
        "2025-04-26T09:45:22.891Z",
        1
    ),
    makeWatchEntry(
        1011,
        "80102411",
        "GLOW",
        "netflix.com/watch/80102411",
        "2025-04-26T12:30:55.234Z",
        2
    ),
    makeWatchEntry(
        1012,
        "70259154",
        "BoJack Horseman",
        "netflix.com/watch/70259154",
        "2025-04-26T15:15:18.678Z",
        3
    ),
    makeWatchEntry(
        1013,
        "80186863",
        "Roma",
        "netflix.com/watch/80186863",
        "2025-04-26T18:00:44.123Z",
        1
    ),
    makeWatchEntry(
        1014,
        "81195050",
        "Bridgerton",
        "netflix.com/watch/81195050",
        "2025-04-26T21:25:33.456Z",
        4
    ),

    // Day 4: 1 entry
    makeWatchEntry(
        1015,
        "81312993",
        "Wednesday",
        "netflix.com/watch/81312993",
        "2025-04-30T19:45:12.789Z",
        1
    ),

    // Day 5: 4 entries
    makeWatchEntry(
        1016,
        "80014749",
        "The Office (US)",
        "netflix.com/watch/80014749",
        "2025-05-01T08:15:31.234Z",
        2
    ),
    makeWatchEntry(
        1017,
        "70300001",
        "Friends",
        "netflix.com/watch/70300001",
        "2025-05-01T12:40:18.567Z",
        3
    ),
    makeWatchEntry(
        1018,
        "70140425",
        "Arrested Development",
        "netflix.com/watch/70140425",
        "2025-05-01T16:22:44.890Z",
        1
    ),
    makeWatchEntry(
        1019,
        "81087914",
        "Squid Game",
        "netflix.com/watch/81087914",
        "2025-05-01T20:55:09.123Z",
        5
    ),

    // Day 6: 2 entries (no entries provided)
    makeWatchEntry(
        1020,
        "81087914411",
        "Lupin",
        "netflix.com/watch/81087914",
        "2025-05-01T20:55:09.123Z",
        5
    ),
    makeWatchEntry(
        1021,
        "81087914422",
        "L'Agernce",
        "netflix.com/watch/81087914",
        "2025-05-01T20:55:09.123Z",
        2
    ),
];
