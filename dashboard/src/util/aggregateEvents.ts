import { TimelineEntrySchema } from "../interface/api.interface";

import { TimelineEvent } from "../interface/weekly.interface";

import { AggregatedTimelineEntry } from "../interface/misc.interface";
/*
 * Aggregates mouse and keyboard windows, in close proximity, into one event.
 * https://claude.ai/chat/65402eae-ee0a-4a2a-81dd-a30866452535
 */
export const aggregateEvents = (
    events: TimelineEntrySchema[],
    threshold: number = 1000
): AggregatedTimelineEntry[] => {
    return events.reduce(
        (acc: AggregatedTimelineEntry[], curr: TimelineEntrySchema, idx) => {
            const lastEvent = acc[acc.length - 1];
            const currStart = new Date(curr.start);
            // Handle first entry separately
            if (idx === 0) {
                acc.push({
                    ...curr,
                    eventCount: 1,
                });
                return acc;
            }
            const lastEnd = new Date(lastEvent.end);
            const timeBetweenEventsIsSmall =
                currStart.getTime() - lastEnd.getTime() < threshold;
            if (lastEvent && timeBetweenEventsIsSmall) {
                // Merge events that are close together
                lastEvent.end = curr.end;
                lastEvent.eventCount = (lastEvent.eventCount || 1) + 1;
            } else {
                // Create new aggregated event
                acc.push({
                    ...curr,
                    eventCount: 1,
                });
            }

            return acc;
        },
        []
    );
};

export const aggregateEventsProgram = (
    events: TimelineEvent[],
    threshold: number = 1000
): TimelineEvent[] => {
    return events.reduce((acc: TimelineEvent[], curr: TimelineEvent, idx) => {
        const lastEvent = acc[acc.length - 1];
        const currStart = new Date(curr.startTime);
        // Handle first entry separately
        if (idx === 0) {
            acc.push({
                ...curr,
            });
            return acc;
        }
        const lastEnd = new Date(lastEvent.endTime);
        const timeBetweenEventsIsSmall =
            currStart.getTime() - lastEnd.getTime() < threshold;
        if (lastEvent && timeBetweenEventsIsSmall) {
            // Merge events that are close together
            lastEvent.endTime = curr.endTime;
        } else {
            // Create new aggregated event
            acc.push({
                ...curr,
            });
        }

        return acc;
    }, []);
};
