import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import { AggregatedTimelineEntry } from "../../interface/misc.interface";

import {
    ProgamUsageTimeline,
    ProgramTimelineContent,
    TimelineEvent,
} from "../../interface/weekly.interface";
import { addEventLinesForPrograms } from "../../util/addEventLines";

import { aggregateEventsProgram } from "../../util/aggregateEvents";

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

        const hourCounts = new Map();
        days.forEach((day: ProgamUsageTimeline) => {
            const dayName = daysOfWeek[new Date(day.date).getDay()];

            // Get the center of the band for the current day
            const yPosition = y(dayName)! + y.bandwidth() / 2;

            const programsSortedByMostTabbedInto = [...day.programs].sort(
                (a, b) => b.events.length - a.events.length
            );

            const topFive = programsSortedByMostTabbedInto.slice(0, 5);

            // Add program events and labels
            topFive.forEach(
                (program: ProgramTimelineContent, programIndex: number) => {
                    // Aggregate events before visualization
                    // FIXME: they're strings before this, but the type says Date, fix the lie
                    const eventsButTheyreRealDates: TimelineEvent[] =
                        program.events.map((event: TimelineEvent) => {
                            return {
                                startTime: new Date(event.startTime),
                                endTime: new Date(event.endTime),
                            };
                        });
                    const aggregatedEvents = aggregateEventsProgram(
                        eventsButTheyreRealDates,
                        10000
                    ); // You might need to adjust the threshold

                    // Count hours for aggregated events
                    aggregatedEvents.forEach((event) => {
                        const date = event.startTime;
                        const hour = date.getHours();
                        const currentCount = hourCounts.get(hour) || 0;
                        hourCounts.set(hour, currentCount + 1);
                    });

                    // Draw program events
                    aggregatedEvents.forEach((event: TimelineEvent) => {
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
        for (let hour = 0; hour < 24; hour++) {
            const count = hourCounts.get(hour) || 0;
            const formattedHour = hour.toString().padStart(2, "0");
            console.log(`${formattedHour}:00 - ${count} events`);
        }
    }, [width, height, margins, days]);

    return (
        <div className="w-full p-4 rounded shadow-lg bg-white">
            <svg ref={svgRef} className="w-full h-full"></svg>
        </div>
    );
};

export default ProgramTimeline;
