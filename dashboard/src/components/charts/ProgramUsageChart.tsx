import React, { useState, useEffect, useRef } from "react";
import * as d3 from "d3";
import {
    DailyProgramSummaries,
    DailyProgramSummary,
} from "../../interface/api.interface";

import { chooseTickValuesSpacing } from "../../util/tickValueSpacing";

interface ProgramUsageChartProps {
    barsInput: DailyProgramSummaries;
}

const ProgramUsageChart: React.FC<ProgramUsageChartProps> = ({ barsInput }) => {
    const [bars, setBars] = useState<DailyProgramSummary[]>([]);

    useEffect(() => {
        if (barsInput) {
            const sortedCols = [...barsInput.columns].sort(
                (a, b) => b.hoursSpent - a.hoursSpent
            );

            const highEnoughTimeVals = sortedCols.filter(
                (col) => col.hoursSpent > 0.1833333
            );
            // FIXME: strange keeping of low time programs
            // setBars(highEnoughTimeVals);
            // if (highEnoughTimeVals.length <= 3) {
            setBars(highEnoughTimeVals);
            // } else {
            // }
        }
    }, [barsInput]);

    const margin = { top: 0, right: 100, bottom: 60, left: 100 };
    const width = 800 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;
    const svgRef = useRef<SVGSVGElement>(null);

    useEffect(() => {
        if (svgRef.current && bars) {
            d3.select(svgRef.current).selectAll("*").remove();

            const svg = d3.select(svgRef.current);

            const xScale = d3
                .scaleBand()
                .domain(bars.map((d) => d.programName))
                .range([0, width])
                .padding(0.5);

            // Get the maximum value and round up to the nearest quarter hour
            const maxHoursSpentValue = d3.max(bars, (d) => d.hoursSpent) || 0;
            const roundedMax = Math.ceil(maxHoursSpentValue * 4) / 4; // Round up to nearest 0.25

            const yScale = d3
                .scaleLinear()
                .domain([0, roundedMax])
                .nice()
                .range([height, 0]);

            svg.selectAll(".bar")
                .data(bars)
                .enter()
                .append("rect")
                .attr("class", "bar")
                .attr("x", (d) => xScale(d.programName) || "fail")
                .attr("y", (d) => yScale(d.hoursSpent))
                .attr("width", xScale.bandwidth())
                .attr("height", (d) => height - yScale(d.hoursSpent))
                .attr("transform", "translate(30, 10)")
                .attr("fill", "steelblue");

            const labelRotation = "-45";
            const xAxis = d3.axisBottom(xScale);
            svg.append("g")
                .attr("class", "x-axis")
                .attr("transform", `translate(30,${height + 10})`)
                .call(xAxis)
                .selectAll("text")
                .style("text-anchor", "end")
                .attr("dx", "-.8em")
                .attr("dy", ".15em")
                .attr("font-size", "1.3em")
                .attr("transform", `rotate(${labelRotation})`);

            const yAxis = d3
                .axisLeft(yScale)
                .tickValues(
                    chooseTickValuesSpacing(maxHoursSpentValue, roundedMax + 1)
                )
                .tickFormat((d) => {
                    const value = +d;
                    // TODO: Handle 0 - 3h, 3 - 6h, 6 - 8h
                    const hours = Math.floor(value);
                    const minutes = Math.round((value - hours) * 60);

                    const limitedUsage = value < 3;
                    const mediumUsage = value < 6;
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

export default ProgramUsageChart;
