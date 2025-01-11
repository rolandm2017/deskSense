import React, { useState, useEffect, useRef } from "react"
import * as d3 from "d3"

const BarChart: React.FC<{}> = ({}) => {
    const [data, setData] = useState([
        { name: "A", value: 50 },
        { name: "B", value: 20 },
        { name: "C", value: 40 },
        { name: "D", value: 70 },
    ])
    // Set up dimensions
    const margin = { top: 0, right: 100, bottom: 30, left: 100 }
    const width = 800 - margin.left - margin.right
    const height = 300 - margin.top - margin.bottom
    const svgRef = useRef<SVGSVGElement>(null)

    useEffect(() => {
        // Create SVG container
        if (svgRef.current) {
            const svg = d3.select(svgRef.current)

            // Create scales
            const xScale = d3
                .scaleBand()
                .domain(data.map((d) => d.name))
                .range([0, width])
                .padding(0.5)
            const yScale = d3
                .scaleLinear()
                .domain([0, d3.max(data, (d) => d.value) || 0])
                .range([height, 0])

            // Create bars
            svg.selectAll(".bar")
                .data(data)
                .enter()
                .append("rect")
                .attr("class", "bar")
                .attr("x", (d) => xScale(d.name) || "fail")
                .attr("y", (d) => yScale(d.value))
                .attr("width", xScale.bandwidth())
                .attr("height", (d) => height - yScale(d.value))
                .attr("transform", "translate(30, 10)")
                .attr("fill", "steelblue")

            // Create x-axis
            const xAxis = d3.axisBottom(xScale)
            svg.append("g")
                .attr("class", "x-axis")
                .attr("transform", `translate(30,${height + 10})`)
                .call(xAxis)

            // Create y-axis
            const yAxis = d3.axisLeft(yScale)
            svg.append("g")
                .attr("class", "y-axis")
                .attr("transform", "translate(30, 10)")
                .call(yAxis)
        }
    }, [])

    return (
        <svg
            ref={svgRef}
            style={{ padding: "100px" }}
            width={width + margin.left + margin.right}
            height={height + margin.top + margin.bottom}
        ></svg>
    )
}

export default BarChart
