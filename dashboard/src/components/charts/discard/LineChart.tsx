// for keyboard and mouse events
import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

interface DataPoint {
    x: number;
    y: number;
}

interface LineChartProps {
    data?: DataPoint[];
    width?: number;
    height?: number;
}

const LineChart: React.FC<LineChartProps> = ({
    data = Array.from({ length: 10 }, (_, i) => ({
        x: i,
        y: Math.random() * 100,
    })),
    width = 600,
    height = 400,
}) => {
    const svgRef = useRef<SVGSVGElement>(null);

    useEffect(() => {
        if (!svgRef.current || !data) return;

        // Clear existing chart
        d3.select(svgRef.current).selectAll("*").remove();

        // Set up margins and dimensions
        const margin = { top: 20, right: 20, bottom: 30, left: 40 };
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;

        // Create scales
        const xScale = d3
            .scaleLinear()
            .domain([0, d3.max(data, (d) => d.x) || 0])
            .range([0, innerWidth]);

        const yScale = d3
            .scaleLinear()
            .domain([0, d3.max(data, (d) => d.y) || 0])
            .range([innerHeight, 0]);

        // Create SVG container
        const svg = d3
            .select(svgRef.current)
            .attr("width", width)
            .attr("height", height);

        // Add chart group and transform it
        const g = svg
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        // Add X axis
        g.append("g")
            .attr("transform", `translate(0,${innerHeight})`)
            .call(d3.axisBottom(xScale))
            .append("text")
            .attr("fill", "black")
            .attr("x", innerWidth / 2)
            .attr("y", 25)
            .text("X Axis");

        // Add Y axis
        g.append("g")
            .call(d3.axisLeft(yScale))
            .append("text")
            .attr("fill", "black")
            .attr("transform", "rotate(-90)")
            .attr("y", -30)
            .attr("text-anchor", "end")
            .text("Y Axis");

        // Add line path
        const line = d3
            .line<DataPoint>()
            .x((d) => xScale(d.x))
            .y((d) => yScale(d.y));

        g.append("path")
            .datum(data)
            .attr("fill", "none")
            .attr("stroke", "steelblue")
            .attr("stroke-width", 2)
            .attr("d", line);

        // Add dots
        g.selectAll("circle")
            .data(data)
            .join("circle")
            .attr("cx", (d) => xScale(d.x))
            .attr("cy", (d) => yScale(d.y))
            .attr("r", 4)
            .attr("fill", "steelblue");
    }, [data, width, height]);

    return (
        <div className="w-full h-full flex items-center justify-center">
            <svg ref={svgRef} className="max-w-full"></svg>
        </div>
    );
};

export default LineChart;
