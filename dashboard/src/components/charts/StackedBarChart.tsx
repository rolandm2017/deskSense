import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import { BreakdownByDay } from "../../interface/weekly.interface";

interface StackedBarChartProps {
    dayByDayBreakdown: BreakdownByDay[];
    title: string;
}

const StackedBarChart: React.FC<StackedBarChartProps> = ({
    dayByDayBreakdown,
    title,
}) => {
    const svgRef = useRef<SVGSVGElement>(null);

    // Set up dimensions
    const margin = { top: 40, right: 30, bottom: 50, left: 60 };
    const width = 800 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    useEffect(() => {
        if (!svgRef.current || !dayByDayBreakdown) return;

        // Clear previous SVG content
        d3.select(svgRef.current).selectAll("*").remove();

        for (const day of dayByDayBreakdown) {
            if (day.productiveHours > 0 || day.leisureHours > 0) {
                console.log("Day: ", day.day);
                console.log("Productive hours: ", day.productiveHours);
                console.log("Leisure hours: ", day.leisureHours);
            }
        }
        // Process the data to get day names
        const processedData = dayByDayBreakdown.map((d) => ({
            day: d.day.toLocaleDateString("en-US", { weekday: "long" }),
            productiveHours: d.productiveHours,
            leisureHours: d.leisureHours,
        }));

        // Stack the data
        const stack = d3
            .stack<any>()
            .keys(["productiveHours", "leisureHours"])
            .order(d3.stackOrderNone)
            .offset(d3.stackOffsetNone);

        const stackedData = stack(processedData);

        // Create scales
        const xScale = d3
            .scaleBand()
            .domain(processedData.map((d) => d.day))
            .range([0, width])
            .padding(0.3);

        const yMax =
            d3.max(processedData, (d) => d.productiveHours + d.leisureHours) ||
            24;
        const yScale = d3
            .scaleLinear()
            .domain([0, Math.min(yMax, 24)])
            .range([height, 0]);

        const softDarkPurple = "#663366";
        const sageGreen = "#96B39A";
        // Create color scale
        const colorScale = d3
            .scaleOrdinal<string>()
            .domain(["productiveHours", "leisureHours"])
            .range([softDarkPurple, sageGreen]);

        // Create chart group
        const svg = d3.select(svgRef.current);
        const g = svg
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        // Add title
        svg.append("text")
            .attr("x", width / 2 + margin.left)
            .attr("y", margin.top / 2)
            .attr("text-anchor", "middle")
            .attr("font-size", "1.2em")
            .attr("font-weight", "bold")
            .text(title);

        // Create stacked bars
        g.selectAll("g.stack")
            .data(stackedData)
            .enter()
            .append("g")
            .attr("class", "stack")
            .attr("fill", (d) => colorScale(d.key))
            .selectAll("rect")
            .data((d) => d)
            .enter()
            .append("rect")
            .attr("x", (d) => xScale(d.data.day) || 0)
            .attr("y", (d) => yScale(d[1]))
            .attr("height", (d) => yScale(d[0]) - yScale(d[1]))
            .attr("width", xScale.bandwidth());

        // Add x-axis
        g.append("g")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(xScale))
            .selectAll("text")
            .attr("font-size", "0.9em")
            .attr("transform", "rotate(-45)")
            .attr("text-anchor", "end")
            .attr("dx", "-0.8em")
            .attr("dy", "0.15em");

        // Add y-axis
        const yAxis = d3
            .axisLeft(yScale)
            .ticks(6)
            .tickFormat((d) => `${d}h`);

        g.append("g").call(yAxis).selectAll("text").attr("font-size", "0.9em");

        // Add y-axis label
        g.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", -40)
            .attr("x", -height / 2)
            .attr("text-anchor", "middle")
            .attr("font-size", "1em")
            .text("Hours");

        // Add legend
        const legend = svg
            .append("g")
            .attr("font-family", "sans-serif")
            .attr("font-size", 10)
            .attr("text-anchor", "start")
            .selectAll("g")
            .data(["Productive Hours", "Leisure Hours"])
            .enter()
            .append("g")
            .attr(
                "transform",
                (d, i) =>
                    `translate(${width + margin.left - 100},${
                        margin.top + i * 20
                    })`
            );

        legend
            .append("rect")
            .attr("x", 0)
            .attr("width", 15)
            .attr("height", 15)
            .attr("fill", (d, i) => (i === 0 ? softDarkPurple : sageGreen));

        legend
            .append("text")
            .attr("x", 20)
            .attr("y", 9.5)
            .attr("dy", "0.32em")
            .text((d) => d);
    }, [dayByDayBreakdown, title]);

    return (
        <svg
            ref={svgRef}
            className="w-full h-full"
            width={width + margin.left + margin.right}
            height={height + margin.top + margin.bottom}
            style={{ overflow: "visible" }}
        />
    );
};

export default StackedBarChart;
