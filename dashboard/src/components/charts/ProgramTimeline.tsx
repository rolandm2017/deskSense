import * as d3 from "d3";
import React, { useEffect, useRef } from "react";

import {
    ProgamUsageTimeline,
    ProgramTimelineContent,
    TimelineEvent,
} from "../../interface/programs.interface";
import { addEventLinesForPrograms } from "../../util/addEventLines";

// https://observablehq.com/@d3/normal-quantile-plot
// https://observablehq.com/@d3/line-chart-missing-data/2
/* ** ** */
/* Current best idea*/
/* ** ** */

interface ProgramTimelineProps {
    days: ProgamUsageTimeline[];
    width?: number;
    height?: number;
    margins?: {
        top: number;
        right: number;
        bottom: number;
        left: number;
    };
}

const ProgramTimeline: React.FC<ProgramTimelineProps> = ({
    days,
    width = 640,
    // height = 384, // Reduced to 0.6 * 640
    // height = 460, // Reduced to (0.6 * 640) * 1.2 = 460
    height = 479, // Reduced to (0.6 * 640) * 1.3 = 499.2
    margins = {
        top: 20,
        right: 80, // Increased right margin to accommodate program names
        bottom: 30,
        left: 60, // Increased left margin to accommodate day names
    },
}) => {
    /*
     *
     * To make this graph tolerate 1,000 data points,
     * The answer is to make zooming in on the map
     * request only the subset of data that is visible within [x1, x2]
     * instead of "oh let's get the whole thing."
     * The uh, the closer the zoom, the smaller
     * the threshold for, for aggregation.
     *
     */
    console.log("TOP OF PROGRAM TIMELOINE TSX");
    const svgRef = useRef<SVGSVGElement | null>(null);

    function addXAxis(
        svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
        x: d3.ScaleTime<number, number, never>,
        customTicks: Date[]
    ) {
        svg.append("g")
            .attr("transform", `translate(0,${height - margins.bottom})`)
            .call(
                d3
                    .axisBottom(x)
                    .tickValues(customTicks)
                    .tickFormat((d: Date | d3.NumberValue) => {
                        if (!(d instanceof Date)) return "";
                        // For 5 AM, return empty string
                        if (d.getHours() === 5) return "";
                        return d3.timeFormat("%I:%M %p")(d);
                    })
            )
            .call((g) => g.select(".domain").remove())
            .call((g) =>
                g
                    .selectAll(".tick line")
                    .clone()
                    .attr("y2", -(height - margins.top - margins.bottom))
                    // .attr("y2", -(height - margins.top - margins.bottom))
                    .attr("stroke-opacity", 0.1)
            )
            .call((g) =>
                g
                    .append("text")
                    .attr("x", width - margins.right)
                    .attr("y", -3)
                    .attr("fill", "currentColor")
                    .attr("font-weight", "bold")
                    .text("Time of Day")
            );
    }

    function addYAxis(
        svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
        y: d3.ScaleBand<string>
    ) {
        svg.append("g")
            .attr("transform", `translate(${margins.left},0)`)
            .call(d3.axisLeft(y))
            .call((g) => g.select(".domain").remove())
            .call((g) =>
                g
                    .selectAll(".tick line")
                    .clone()
                    .attr("x2", width - margins.left - margins.right)
                    .attr("stroke-opacity", 0.1)
            );
    }

    useEffect(() => {
        if (!svgRef.current) return;

        d3.select(svgRef.current).selectAll("*").remove();

        const startHour = 5; // outside of debugging, use 5 (5:00 am)
        const endHour = 23; // outside of debugging, use 23 (11:59 pm)
        const endMinute = 59;

        const x: d3.ScaleTime<number, number, never> = d3
            .scaleTime()
            .domain([
                new Date(2024, 0, 1, startHour, 0), // 5 AM
                new Date(2024, 0, 1, endHour, endMinute), // 11:59 PM
            ])
            .nice()
            .range([margins.left, width - margins.right]);

        // Define days of week in order (Sunday at top)
        const daysOfWeek = [
            // FIXME: The W in "Wed" is cut off.
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ];

        // Create y scale using band scale for categorical data
        const reducedIrrelevantSpaceForSunday = 30;
        const offsetForTopOfGrid =
            margins.top - reducedIrrelevantSpaceForSunday;
        const additionalSpaceForSaturday = 20;
        const offsetForBottomOfGrid =
            height - margins.bottom - additionalSpaceForSaturday;
        const y: d3.ScaleBand<string> = d3
            .scaleBand()
            .domain(daysOfWeek)
            .range([offsetForTopOfGrid, offsetForBottomOfGrid])
            .padding(0.1);

        const svg: d3.Selection<SVGSVGElement, unknown, null, undefined> = d3
            .select(svgRef.current)
            .attr("viewBox", [0, 0, width, height])
            .attr("width", width)
            .attr("height", height)
            .style("max-width", "100%")
            .style("height", "auto");

        // Create custom ticks: 5 AM, 6 AM, then every 3 hours until midnight
        const customTicks: Date[] = [
            new Date(2024, 0, 1, 5, 0), // 5 AM
            new Date(2024, 0, 1, 6, 0), // 6 AM
            new Date(2024, 0, 1, 9, 0), // 9 AM
            new Date(2024, 0, 1, 12, 0), // 12 PM
            new Date(2024, 0, 1, 15, 0), // 3 PM
            new Date(2024, 0, 1, 18, 0), // 6 PM
            new Date(2024, 0, 1, 21, 0), // 9 PM
            new Date(2024, 0, 1, 23, 59), // 11:59 PM
        ];

        addXAxis(svg, x, customTicks);

        addYAxis(svg, y);

        // Add y-axis

        // Add timeline events as lines
        const eventLines: d3.Selection<SVGGElement, unknown, null, undefined> =
            svg.append("g").attr("class", "event-lines");

        // Add a group for program labels
        const programLabels: d3.Selection<
            SVGGElement,
            unknown,
            null,
            undefined
        > = svg.append("g").attr("class", "program-labels");

        const baseRowSpacing = 60;

        function calculateMouseRowPosition(dayNumber: number) {
            // old version: 20 * dayNumber
            return baseRowSpacing * dayNumber + 10;
        }

        function calculateKeyboardRowPosition(dayNumber: number) {
            // old version:  20 * dayNumber + 10
            return baseRowSpacing * dayNumber + 20;
        }

        /*
         * 20 = very top of the range, y = 120
         * 608 = about y = 0
         * Claude says it's because of SVG coordinate system being reversed
         */

        // Process days and draw lines and labels

        // TODO: Group days.events by ProgramName, and then for each program, ... draw the line
        // TODO: Draw a highlight for lines that show double counting.

        const startHourCounts = new Map();
        const endHourCounts = new Map();
        let longestDuration = 0;
        let longestDurationProgram = null;
        let longestDurationEvent = null;
        const durationArr: number[] = [];
        const windowsTerminalByDuration: any[] = [];
        days.forEach((day: ProgamUsageTimeline) => {
            const dayName = daysOfWeek[new Date(day.date).getDay()];
            if ("Monday" != dayName) {
                return;
            }

            // Get the center of the band for the current day
            const yPosition = y(dayName)! + y.bandwidth() / 2;

            const programsSortedByMostTabbedInto = [...day.programs].sort(
                (a, b) => b.events.length - a.events.length
            );

            const topFive = programsSortedByMostTabbedInto.slice(0, 5);

            // Add program events and labels
            topFive.forEach(
                (program: ProgramTimelineContent, programIndex: number) => {
                    // if (!program.programName.includes("Windows")) {
                    //     return;
                    // }
                    // Aggregate events before visualization
                    // FIXME: they're strings before this, but the type says Date, fix the lie
                    const eventsButTheyreRealDates: TimelineEvent[] =
                        program.events
                            .map((event: TimelineEvent) => {
                                return {
                                    startTime: new Date(event.startTime),
                                    endTime: new Date(event.endTime),
                                };
                            })
                            .filter((event: TimelineEvent) => {
                                // remove events that clearly are bad data
                                const endTime = event.endTime.getHours();
                                const earliestEverUsage = 6;
                                const latestEverUsage = 22;
                                if (
                                    endTime < earliestEverUsage ||
                                    endTime > latestEverUsage
                                ) {
                                    return;
                                }
                                const startTime = event.startTime.getHours();
                                if (
                                    startTime < earliestEverUsage ||
                                    startTime > latestEverUsage
                                ) {
                                    console.log(
                                        `Eliminated because it was at ${startTime}`
                                    );
                                    return;
                                }
                                return event;
                            });
                    // const eventsToProcess =
                    //     eventsButTheyreRealDates.length > 100
                    //         ? eventsButTheyreRealDates.filter(
                    //               (_, i) => i % 2 === 0
                    //           ) // Take every 5th event
                    //         : eventsButTheyreRealDates;
                    const aggregatedEvents = eventsButTheyreRealDates;
                    // const aggregatedEvents = aggregateEventsProgram(
                    //     eventsToProcess,
                    //     2000
                    // ); // You might need to adjust the threshold

                    // Count hours for aggregated events
                    aggregatedEvents.forEach((event: TimelineEvent) => {
                        const date = event.startTime;
                        const startHour = date.getHours();

                        const currentCount =
                            startHourCounts.get(startHour) || 0;
                        startHourCounts.set(startHour, currentCount + 1);

                        const endHour = event.endTime.getHours();
                        const currentEndCount = endHourCounts.get(endHour) || 0;
                        endHourCounts.set(endHour, currentEndCount + 1);

                        // Get duration in milliseconds
                        const durationMs =
                            event.endTime.getTime() - event.startTime.getTime();

                        if (durationMs > longestDuration) {
                            longestDuration = durationMs;
                            longestDurationProgram = program;
                            longestDurationEvent = event;
                        }
                    });

                    // Draw program events
                    aggregatedEvents.forEach((event: TimelineEvent) => {
                        // if (dayName.includes("Sat")) {
                        //     console.log(event, "302ru");
                        // }
                        // if (
                        //     event.startTime.getHours() < 11 ||
                        //     event.startTime.getHours() > 16 ||
                        //     event.endTime.getHours() > 16
                        // ) {
                        //     return;
                        // }
                        const durationMs =
                            event.endTime.getTime() - event.startTime.getTime();

                        durationArr.push(durationMs);
                        if (durationMs < 0) {
                            console.log(program.programName);
                            console.log(event, durationMs);
                            if (durationMs < 2000) {
                                throw new Error("Negative duration error");
                            }
                        }

                        if (durationMs > longestDuration) {
                            longestDuration = durationMs;
                            longestDurationProgram = program;
                            longestDurationEvent = event;
                        }
                        windowsTerminalByDuration.push({
                            duration: durationMs,
                            event,
                        });

                        // // if (event.endTime.getHours() < 19) {  // odd times gone
                        // console.log(event.startTime.getHours(), "265ru");
                        addEventLinesForPrograms(
                            yPosition + programIndex * 10,
                            program.programName,
                            event,
                            eventLines,
                            x,
                            y
                        );
                    });

                    // Add program name label at the right edge
                    programLabels
                        .append("text")
                        .attr("x", width - margins.right + 10) // Position text slightly right of the graph
                        .attr("y", yPosition + programIndex * 10) // Align with the corresponding program line
                        .attr("dy", "0.35em") // Vertical centering of text
                        .attr("font-size", "10px") // Smaller font size
                        .attr("text-anchor", "start") // Left-align text
                        .attr("fill", "currentColor")
                        .text(program.programName);
                }
            );
        });
        // Output the results in order from 0 to 23
        // console.log("START TIME MAP:");
        // for (let hour = 0; hour < 24; hour++) {
        //     const count = startHourCounts.get(hour) || 0;
        //     const formattedHour = hour.toString().padStart(2, "0");
        //     console.log(`${formattedHour}:00 - ${count} events`);
        // }
        console.log("END TIME MAP:");
        for (let hour = 0; hour < 24; hour++) {
            const count = endHourCounts.get(hour) || 0;
            const formattedHour = hour.toString().padStart(2, "0");
            console.log(`${formattedHour}:00 - ${count} events`);
        }
        console.log("longest duration:", longestDuration);
        console.log(longestDurationProgram);
        console.log(longestDurationEvent);
        windowsTerminalByDuration.sort((a, b) => b.duration - a.duration);
        let i = 0;
        for (const event of windowsTerminalByDuration) {
            console.log(event);
            i++;
            if (i > 10) {
                break;
            }
        }
    }, [width, height, margins, days]);

    return (
        <div className="w-full p-4 rounded shadow-lg bg-white">
            <svg ref={svgRef} className="w-full h-full"></svg>
        </div>
    );
};

export default ProgramTimeline;
