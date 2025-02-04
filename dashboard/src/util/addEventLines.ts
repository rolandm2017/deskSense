import { Selection, ScaleLinear } from "d3";

import { AggregatedTimelineEntry } from "../interface/misc.interface";

export function addEventLines(
    yPosition: number, // 50, 60
    entry: AggregatedTimelineEntry,
    eventLines: Selection<SVGGElement, unknown, null, undefined>,
    x: ScaleLinear<number, number, never>,
    y: ScaleLinear<number, number, never>
) {
    const startX = x(dateToX(entry.start));
    const endX = x(dateToX(entry.end));

    // Add the line for the event
    eventLines
        .append("line")
        .attr("x1", startX)
        .attr("x2", endX)
        .attr("y1", yPosition)
        .attr("y2", yPosition)
        .attr("stroke", entry.group === "mouse" ? "steelblue" : "#e41a1c")
        .attr("stroke-width", 2)
        .attr("stroke-opacity", 0.7);

    // Add small circles at start and end points
    eventLines
        .append("circle")
        .attr("cx", startX)
        .attr("cy", yPosition)
        .attr("r", 2)
        .attr("fill", entry.group === "mouse" ? "steelblue" : "#e41a1c");

    eventLines
        .append("circle")
        .attr("cx", endX)
        .attr("cy", yPosition)
        .attr("r", 2)
        .attr("fill", entry.group === "mouse" ? "steelblue" : "#e41a1c");
}

// Helper function to map Date to x position (-3 to 3)
function dateToX(date: Date | string | { toString: () => string }): number {
    // Ensure we're working with a proper Date object
    const dateObj = date instanceof Date ? date : new Date(date.toString());
    const midnight = new Date(dateObj);
    midnight.setHours(0, 0, 0, 0);
    const endOfDay = new Date(dateObj);
    endOfDay.setHours(23, 59, 59, 999);

    // Calculate position between -3 and 3 based on time of day
    // console.log(
    //     endOfDay,
    //     Object.prototype.toString.call(endOfDay) === "[object Date]",
    //     "46ru"
    // );

    const totalMs = endOfDay.getTime() - midnight.getTime();
    const currentMs = dateObj.getTime() - midnight.getTime();
    return -3 + (currentMs / totalMs) * 6;
}
