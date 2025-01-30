import React, { useState, useEffect, useRef } from "react";
import * as d3 from "d3";
import {
    DailyChromeSummaries,
    DailyChromeSummary,
} from "../../interface/api.interface";

import { chooseTickValuesSpacing } from "../../util/tickValueSpacing";

interface ChromeUsageChartProps {
    barsInput: DailyChromeSummaries;
}

const ChromeUsageChart: React.FC<ChromeUsageChartProps> = ({ barsInput }) => {
    const [bars, setBars] = useState<DailyChromeSummary[]>([]);

    useEffect(() => {
        if (barsInput) {
            // console.log(barsInput, "18ru");
            const sortedCols = [...barsInput.columns].sort(
                (a, b) => b.hoursSpent - a.hoursSpent
            );
            console.log(
                sortedCols.map((col) => Number(col.hoursSpent.toFixed(5))),
                "Chrome - hours spent"
            );
            const highEnoughTimeVals = sortedCols.filter(
                (col) => col.hoursSpent > 0.0833333 // 5 / 60 = 0.08333
            );
            if (highEnoughTimeVals.length <= 4) {
                // TODO If the AVERAGE time of the top 4 entries is LESS than 1 hour, show ALL entries
                setBars(sortedCols);
            } else {
                setBars(highEnoughTimeVals);
            }
        }
    }, [barsInput]);

    // Set up dimensions
    const margin = { top: 0, right: 100, bottom: 60, left: 100 }; // Increased bottom margin
    const width = 800 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;
    const svgRef = useRef<SVGSVGElement>(null);

    // FIXME: If tallest bar = 2h20m, should get maxYVal as 2h30m. Currently 2h30m -> 3h max y val, that's bad.
    // FIXME: graph also shows places with a hoursSpent less than 15 min. that's bad

    useEffect(() => {
        if (svgRef.current && bars) {
            // Clear previous SVG content
            d3.select(svgRef.current).selectAll("*").remove();

            const svg = d3.select(svgRef.current);

            // Create scales
            const xScale = d3
                .scaleBand()
                .domain(bars.map((d) => d.domainName))
                .range([0, width])
                .padding(0.5);

            const ceilingedMaxHours = Math.ceil(
                Math.max(...bars.map((bar) => bar.hoursSpent))
            );
            // Y Scale (Time Scale)
            const yScale = d3
                .scaleLinear()
                .domain([0, ceilingedMaxHours]) // Use hoursSpent as is
                .range([height, 0]);

            // Create bars
            svg.selectAll(".bar")
                .data(bars)
                .enter()
                .append("rect")
                .attr("class", "bar")
                .attr("x", (d) => xScale(d.domainName) || "fail")
                .attr("y", (d) => yScale(d.hoursSpent))
                .attr("width", xScale.bandwidth())
                .attr("height", (d) => height - yScale(d.hoursSpent))
                .attr("transform", "translate(30, 10)")
                .attr("fill", "steelblue");

            // Create x-axis with rotated labels
            const labelRotation = "-45";
            const xAxis = d3.axisBottom(xScale);
            svg.append("g")
                .attr("class", "x-axis")
                .attr("transform", `translate(30,${height + 10})`)
                .call(xAxis)
                .selectAll("text") // Select all x-axis text elements
                .style("text-anchor", "end") // Anchor point for the text
                .attr("dx", "-.8em") // Shift text position
                .attr("dy", ".15em") // Shift text position
                .attr("font-size", "1.3em")
                .attr("transform", `rotate(${labelRotation})`); // Rotate text 45 degrees

            const maxHours = Math.ceil(
                d3.max(bars.map((bar) => bar.hoursSpent)) || 0
            );

            const yAxis = d3
                .axisLeft(yScale)
                .tickValues(
                    chooseTickValuesSpacing(ceilingedMaxHours, maxHours)
                ) // Custom tick values
                .tickFormat((d) => {
                    const value = +d; // Convert to plain number
                    const hours = Math.floor(value);
                    const minutes = Math.round((value - hours) * 60);
                    // const highUsage = value >= 6;
                    if (hours > 0 && minutes === 0) {
                        return `${hours}h`;
                    } else if (hours > 0) {
                        return `${hours}h ${minutes} min`;
                    } else {
                        return `${minutes} min`;
                    }
                });

            svg.append("g")
                .attr("class", "y-axis")
                .attr("transform", "translate(30, 10)")
                .call(yAxis);

            // Add y-axis label
            svg.append("text")
                .attr("transform", "rotate(-90)") // Rotate text to be vertical
                .attr("y", -50)
                .attr("x", -(height / 2)) // Center on the axis
                .attr("dy", "1em") // Shift the text position
                .style("text-anchor", "middle") // Center the text
                .attr("font-size", "1.2em")
                .text("Hours"); // The label text
        }
    }, [bars]);

    return (
        <svg
            ref={svgRef}
            style={{
                padding: "100px 100px 200px 100px",
                border: "3px solid red",
                overflow: "visible",
            }}
            width={width + margin.left + margin.right}
            height={height + margin.top + margin.bottom}
        ></svg>
    );
};

export default ChromeUsageChart;
