import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

import { BarChartDayData } from "../../interface/misc.interface";

interface WeeklyUsageChartProps {
    data: BarChartDayData[];
    title: string;
}

const WeeklyUsageChart: React.FC<WeeklyUsageChartProps> = ({ data, title }) => {
    // FIXME: On Feb 20, I observed the program stating that I was
    // FIXME: on Twitter for 10h sunday, 13h Monday. Obviously not true. Hence
    // FIXME: Twitter sessions is being left open while I shut the computer down
    console.log(data, "12ru");
    const svgRef = useRef<SVGSVGElement>(null);

    // Set up dimensions
    const margin = { top: 40, right: 30, bottom: 50, left: 60 };
    const width = 800 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    const days = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ];

    useEffect(() => {
        if (!svgRef.current || !data) return;

        // Clear previous SVG content
        d3.select(svgRef.current).selectAll("*").remove();

        const svg = d3.select(svgRef.current);

        // Process data to include all days (with 0 for missing days)
        const processedData = days.map((dayName) => {
            const dayData = data.find((d) => {
                const dateDayName = d.day.toLocaleDateString("en-US", {
                    weekday: "long",
                });
                return dateDayName === dayName;
            });
            return {
                day: dayName,
                hours: dayData ? dayData.hoursSpent : 0,
            };
        });

        // Create scales
        const xScale = d3
            .scaleBand()
            .domain(days)
            .range([0, width])
            .padding(0.3);

        const maxHours = Math.max(...processedData.map((d) => d.hours));
        const yScale = d3
            .scaleLinear()
            .domain([0, Math.min(Math.max(maxHours, 1), 14)]) // Max of 14 hours, min of actual max or 1
            .range([height, 0]);

        // Create chart group
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

        // Create bars
        g.selectAll(".bar")
            .data(processedData)
            .enter()
            .append("rect")
            .attr("class", "bar")
            .attr("x", (d) => xScale(d.day) || 0)
            .attr("y", (d) => (d.hours ? yScale(d.hours) : height))
            .attr("width", xScale.bandwidth())
            .attr("height", (d) => (d.hours ? height - yScale(d.hours) : 0))
            .attr("fill", "steelblue")
            .attr("opacity", (d) => (d.hours ? 1 : 0)); // Hide bars with 0 hours

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
    }, [data, title]);

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

export default WeeklyUsageChart;
