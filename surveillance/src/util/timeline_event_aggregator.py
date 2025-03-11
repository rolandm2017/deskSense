
from typing import List

from ..db.models import TimelineEntryObj, PrecomputedTimelineEntry


# /*
#  * Aggregates mouse and keyboard windows, in close proximity, into one event.
#  * https://claude.ai/chat/65402eae-ee0a-4a2a-81dd-a30866452535
#  */

four_sec = 4000
# Note: I believe a four sec gap is good because,
# nobody stops typing, gets up for a sec, sits back down and resumes typing, in four sec.
# Further, a pause to check your phone probably lasts at least 4 sec.
# --> What about thinking gaps? "I paused to think it through"
# Okay, so make it six sec.
three_sec = 3000

# NOTE: Okay so, I tried four sec, it was too vast of a width to yield a linkage. Better one sec.
# NOTE #2: Even 1000 ms seems a little too long. Trying 500 ms.
half_sec = 500


def aggregate_timeline_events(events: List[TimelineEntryObj], threshold=half_sec) -> List[PrecomputedTimelineEntry]:
    acc = []
    for i in range(0, len(events)):
        if i == 0:
            first_obj = events[i]
            first_compressed_obj = PrecomputedTimelineEntry(clientFacingId=first_obj.clientFacingId, group=first_obj.group,
                                                            content=first_obj.content, start=first_obj.start, end=first_obj.end, eventCount=1)
            acc.append(first_compressed_obj)
            continue
        last_event = acc[len(acc) - 1]
        last_end = last_event.end
        # const timeBetweenEventsIsSmall = currStart.getTime() - lastEnd.getTime() < threshold;
        current = events[i]
        time_between_events_is_small = current.start.timestamp(
        ) - last_end.timestamp() < threshold
        if last_end and time_between_events_is_small:
            # // Merge events that are close together
            last_event.end = current.end
            last_event.eventCount = last_event.eventCount + 1
        else:
            compressed_obj = PrecomputedTimelineEntry(clientFacingId=current.clientFacingId, group=current.group,
                                                      content=current.content, start=current.start, end=current.end, eventCount=1)
            acc.append(compressed_obj)
    return acc

# From
# dashboard/src/util/aggregateEvents.ts

# export const aggregateEvents = (
#     events: TimelineEntrySchema[],
#     threshold: number = 1000
# ): AggregatedTimelineEntry[] => {
#     return events.reduce((acc: AggregatedTimelineEntry[], curr, idx) => {
#         const lastEvent = acc[acc.length - 1];
#         const currStart = new Date(curr.start);
#         // Handle first entry separately
#         if (idx === 0) {
#             acc.push({
#                 ...curr,
#                 eventCount: 1,
#             });
#             return acc;
#         }
#         const lastEnd = new Date(lastEvent.end);
#         if (lastEvent && currStart.getTime() - lastEnd.getTime() < threshold) {
#             // Merge events that are close together
#             lastEvent.end = curr.end;
#             lastEvent.eventCount = (lastEvent.eventCount || 1) + 1;
#         } else {
#             // Create new aggregated event
#             acc.push({
#                 ...curr,
#                 eventCount: 1,
#             });
#         }

#         return acc;
#     }, []);
# };
