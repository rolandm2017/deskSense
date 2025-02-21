import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import { AggregatedTimelineEntry } from "../../interface/misc.interface";
import { addEventLines } from "../../util/addEventLines";

// https://observablehq.com/@d3/normal-quantile-plot
// https://observablehq.com/@d3/line-chart-missing-data/2
/* ** ** */
/* Current best idea*/
/* ** ** */

interface QQPlotProps {
    mouseEvents: AggregatedTimelineEntry[];
    keyboardEvents: AggregatedTimelineEntry[];
    width?: number;
    height?: number;
    margins?: {
        top: number;
        right: number;
        bottom: number;
        left: number;
    };
}

const QQPlotV2Single: React.FC<QQPlotProps> = ({
    mouseEvents,
    keyboardEvents,
    width = 640,
    height = 640,
    margins = {
        top: 20,
        right: 40,
        bottom: 30,
        left: 40,
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
    console.log(mouseEvents.length, keyboardEvents.length, "35ru");
    const svgRef = useRef<SVGSVGElement | null>(null);

    useEffect(() => {
        if (!svgRef.current) return;

        d3.select(svgRef.current).selectAll("*").remove();

        const x = d3
            .scaleLinear()
            .domain([-3, 3])
            .nice()
            .range([margins.left, width - margins.right]);

        const y = d3
            .scaleLinear()
            .domain([0, 120])
            .nice()
            .range([height - margins.bottom, margins.top]);

        const svg = d3
            .select(svgRef.current)
            .attr("viewBox", [0, 0, width, height])
            .attr("width", width)
            .attr("height", height)
            .style("max-width", "100%")
            .style("height", "auto");

        // Add x-axis (time of day)
        svg.append("g")
            .attr("transform", `translate(0,${height - margins.bottom})`)
            .call(d3.axisBottom(x))
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

        /*
         * 20 = very top of the range, y = 120
         * 608 = about y = 0
         * Claude says it's because of SVG coordinate system being reversed
         */
        mouseEvents.forEach((entry: AggregatedTimelineEntry) => {
            // FIXME: migrate this to be time on x
            addEventLines(20, entry, eventLines, x, y);
        });
        keyboardEvents.forEach((entry: AggregatedTimelineEntry) => {
            addEventLines(608, entry, eventLines, x, y);
        });
    }, [width, height, margins, mouseEvents]);

    return (
        <div className="w-full p-4 rounded shadow-lg bg-white">
            <svg ref={svgRef} className="w-full h-full"></svg>
        </div>
    );
};

export default QQPlotV2Single;
