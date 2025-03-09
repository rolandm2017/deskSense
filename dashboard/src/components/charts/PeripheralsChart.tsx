import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import {
    AggregatedTimelineEntry,
    DayOfAggregatedRows,
} from "../../interface/misc.interface";

import { DayOfChromeUsage } from "../../interface/weekly.interface";
import { addEventLines } from "../../util/addEventLines";

// https://observablehq.com/@d3/normal-quantile-plot
// https://observablehq.com/@d3/line-chart-missing-data/2
/* ** ** */
/* Current best idea*/
/* ** ** */

interface PeripheralsChartProps {
    days: DayOfAggregatedRows[];
    width?: number;
    height?: number;
    margins?: {
        top: number;
        right: number;
        bottom: number;
        left: number;
    };
}

const PeripheralsChart: React.FC<PeripheralsChartProps> = ({
    days,
    width = 640,
    height = 384, // Reduced to 0.6 * 640
    margins = {
        top: 20,
        right: 40,
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
    // console.log(days.length, "35ru");

    const svgRef = useRef<SVGSVGElement | null>(null);

    useEffect(() => {
        if (!svgRef.current) return;

        d3.select(svgRef.current).selectAll("*").remove();

        const x = d3
            .scaleTime()
            .domain([
                new Date(2024, 0, 1, 5, 0), // 5 AM
                new Date(2024, 0, 1, 23, 59), // 11:59 PM
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
        const y = d3
            .scaleBand()
            .domain(daysOfWeek)
            .range([margins.top, height - margins.bottom])
            .padding(0.1);

        const svg = d3
            .select(svgRef.current)
            .attr("viewBox", [0, 0, width, height])
            .attr("width", width)
            .attr("height", height)
            .style("max-width", "100%")
            .style("height", "auto");

        // Create custom ticks: 5 AM, 6 AM, then every 3 hours until midnight
        const customTicks = [
            new Date(2024, 0, 1, 5, 0), // 5 AM
            new Date(2024, 0, 1, 6, 0), // 6 AM
            new Date(2024, 0, 1, 9, 0), // 9 AM
            new Date(2024, 0, 1, 12, 0), // 12 PM
            new Date(2024, 0, 1, 15, 0), // 3 PM
            new Date(2024, 0, 1, 18, 0), // 6 PM
            new Date(2024, 0, 1, 21, 0), // 9 PM
            new Date(2024, 0, 1, 23, 59), // 11:59 PM
        ];

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

        // Add y-axis
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

        // Add timeline events as lines
        const eventLines: d3.Selection<SVGGElement, unknown, null, undefined> =
            svg.append("g").attr("class", "event-lines");

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

        days.forEach((day: DayOfAggregatedRows) => {
            // console.log(day.date, "126ru");
            const dayName = daysOfWeek[new Date(day.date).getDay()];

            // Get the center of the band for the current day
            const yPosition = y(dayName)! + y.bandwidth() / 2;

            // Add mouse events
            day.mouseRow.forEach((event: AggregatedTimelineEntry) => {
                addEventLines(yPosition, event, eventLines, x, y);
            });

            // Add keyboard events slightly below mouse events
            day.keyboardRow.forEach((event: AggregatedTimelineEntry) => {
                addEventLines(yPosition + 10, event, eventLines, x, y);
            });
        });
    }, [width, height, margins, days]);

    return (
        <div className="w-full p-4 rounded shadow-lg bg-white">
            <svg ref={svgRef} className="w-full h-full"></svg>
        </div>
    );
};

export default PeripheralsChart;
