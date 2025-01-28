import React, { useState, useEffect, useRef } from "react";
import * as d3 from "d3";
import { BarChartColumn } from "../../interface/misc.interface";
import {
    DailyChromeSummaries,
    DailyChromeSummary,
} from "../../api/getData.api";

interface ChromeUsageChartProps {
    barsInput: DailyChromeSummaries;
}

const ChromeUsageChart: React.FC<ChromeUsageChartProps> = ({ barsInput }) => {
    const [bars, setBars] = useState<DailyChromeSummary[]>([]);

    useEffect(() => {
        if (barsInput) {
            const sortedCols = [...barsInput.columns].sort(
                (a, b) => b.hoursSpent - a.hoursSpent
            );
            console.log(
                sortedCols.map((col) => Number(col.hoursSpent.toFixed(5))),
                "hours spent"
            );
            const highEnoughTimeVals = sortedCols.filter(
                (col) => col.hoursSpent > 0.015
            );
            setBars(highEnoughTimeVals);
        }
    }, [barsInput]);

    // Set up dimensions
    const margin = { top: 0, right: 100, bottom: 60, left: 100 }; // Increased bottom margin
    const width = 800 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;
    const svgRef = useRef<SVGSVGElement>(null);

    useEffect(() => {
        if (svgRef.current && bars) {
            // Clear previous SVG content
            d3.select(svgRef.current).selectAll("*").remove();

            const svg = d3.select(svgRef.current);

            // Create scales
            const xScale = d3
                .scaleBand()
                .domain(bars.map((d) => d.domain))
                .range([0, width])
                .padding(0.5);
            const yScale = d3
                .scaleLinear()
                .domain([0, d3.max(bars, (d) => d.hoursSpent) || 0])
                .nice()
                .range([height, 0]);

            // Create bars
            svg.selectAll(".bar")
                .data(bars)
                .enter()
                .append("rect")
                .attr("class", "bar")
                .attr("x", (d) => xScale(d.domain) || "fail")
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

            // Create y-axis
            const yAxis = d3.axisLeft(yScale);
            svg.append("g")
                .attr("class", "y-axis")
                .attr("transform", "translate(30, 10)")
                .call(yAxis);
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
