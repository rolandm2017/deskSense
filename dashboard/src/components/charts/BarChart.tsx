import React, { useState, useEffect, useRef } from "react";
import * as d3 from "d3";
import { ProgramActivityReport } from "../../interface/api.interface";
import { BarChartColumn } from "../../interface/misc.interface";

interface BarChartProps {
    barsInput: BarChartColumn[];
}

const BarChart: React.FC<BarChartProps> = ({ barsInput }) => {
    // TODO: foo foo, get inputs. { barTitle: programName, hoursSpent: float }
    // TODO: make the array

    const oldData = [
        { programName: "Chrome", hoursSpent: 6.5 },
        { programName: "Discord", hoursSpent: 3.3 },
        { programName: "VSCode", hoursSpent: 2.2 },
        { programName: "Postman", hoursSpent: 4.8 },
    ];
    const [bars, setBars] = useState<BarChartColumn[]>([]);

    // Set up dimensions
    const margin = { top: 0, right: 100, bottom: 30, left: 100 };
    const width = 800 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;
    const svgRef = useRef<SVGSVGElement>(null);

    useEffect(() => {
        console.log(barsInput.length, "19ru");
        if (barsInput.length !== 0) {
            console.log("setting bars input", "31ru");
            setBars(barsInput);
        }
    }, [barsInput]);

    useEffect(() => {
        // Create SVG container
        if (svgRef.current) {
            const svg = d3.select(svgRef.current);

            // Create scales
            const xScale = d3
                .scaleBand()
                .domain(bars.map((d) => d.programName))
                .range([0, width])
                .padding(0.5);
            const yScale = d3
                .scaleLinear()
                .domain([0, d3.max(bars, (d) => d.hoursSpent) || 0])
                .range([height, 0]);

            // Create bars
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

            // Create x-axis
            const xAxis = d3.axisBottom(xScale);
            svg.append("g")
                .attr("class", "x-axis")
                .attr("transform", `translate(30,${height + 10})`)
                .call(xAxis);

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
            style={{ padding: "100px" }}
            width={width + margin.left + margin.right}
            height={height + margin.top + margin.bottom}
        ></svg>
    );
};

export default BarChart;
