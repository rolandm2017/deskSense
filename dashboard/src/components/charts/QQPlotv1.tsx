import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

interface QQPlotProps {
    width?: number;
    height?: number;
    color1?: string;
    color2?: string;
    margins?: {
        top: number;
        right: number;
        bottom: number;
        left: number;
    };
}

const normalQuantile = (p: number): number => {
    const mu = 0;
    const sigma = 1;
    const a = 0.147;
    const ierf = (x: number): number => {
        const signX = x < 0 ? -1 : 1;
        const absX = Math.abs(x);

        if (absX > 0.7) {
            const z = Math.sqrt(-Math.log((1 - absX) / 2));
            return (
                signX *
                    ((((-0.000200214257 * z + 0.000100950558) * z +
                        0.00134934322) *
                        z -
                        0.00367342844) *
                        z +
                        0.00573950773) *
                    z -
                0.0076224613
            );
        }

        const z = x * x;
        return (
            x *
            (((1.750277447 * z + 2.369951582) * z + 2.312635686) * z +
                1.501321109)
        );
    };

    return mu + sigma * Math.sqrt(2) * ierf(2 * p - 1);
};

const QQPlot: React.FC<QQPlotProps> = ({
    width = 640,
    height = 640,
    color1 = "steelblue",
    color2 = "#e41a1c",
    margins = {
        top: 20,
        right: 40,
        bottom: 30,
        left: 40,
    },
}) => {
    const svgRef = useRef<SVGSVGElement | null>(null);

    const plotHorizontalLine = (
        yValue: number,
        color: string = "black",
        x: d3.ScaleLinear<number, number, never>,
        y: d3.ScaleLinear<number, number, never>,
        z: (i: number) => number
    ) => {
        const n = 100;
        const opacity = 0.3;
        const svg = d3.select(svgRef.current);

        svg.append("line")
            .attr("stroke", color)
            .attr("stroke-opacity", opacity)
            .attr("x1", margins.left)
            .attr("x2", width - margins.right)
            .attr("y1", y(yValue))
            .attr("y2", y(yValue));

        // Add points along the line
        svg.append("g")
            .attr("fill", "none")
            .attr("stroke", color)
            .attr("stroke-width", 1.5)
            .selectAll("circle")
            .data(d3.range(n))
            .join("circle")
            .attr("cx", (i) => x(z(i)))
            .attr("cy", (i) => y(yValue))
            .attr("r", 3);
    };

    useEffect(() => {
        if (!svgRef.current) return;

        d3.select(svgRef.current).selectAll("*").remove();

        const n = 100;
        const z = (i: number): number => normalQuantile((i + 0.5) / n);
        const qy1: number[] = Array(n).fill(60);
        const qy2: number[] = Array(n).fill(55);

        const x = d3
            .scaleLinear()
            .domain([-3, 3])
            .nice()
            .range([margins.left, width - margins.right]);

        const y: d3.ScaleLinear<number, number, never> = d3
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

        // Add x-axis
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
                    .text("z")
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
            )
            .call((g) =>
                g
                    .select(".tick:last-of-type text")
                    .clone()
                    .attr("x", 3)
                    .attr("text-anchor", "start")
                    .attr("font-weight", "bold")
                    .text("Strength")
            );

        // Add horizontal lines
        svg.append("line")
            .attr("stroke", color1)
            .attr("stroke-opacity", 0.3)
            .attr("x1", margins.left)
            .attr("x2", width - margins.right)
            .attr("y1", y(60))
            .attr("y2", y(60));

        svg.append("line")
            .attr("stroke", color2)
            .attr("stroke-opacity", 0.3)
            .attr("x1", margins.left)
            .attr("x2", width - margins.right)
            .attr("y1", y(55))
            .attr("y2", y(55));

        // Add first set of points (y=60)
        svg.append("g")
            .attr("fill", "none")
            .attr("stroke", color1)
            .attr("stroke-width", 1.5)
            .selectAll("circle")
            .data(d3.range(n))
            .join("circle")
            .attr("cx", (i) => x(z(i)))
            .attr("cy", (i) => y(qy1[i]))
            .attr("r", 3);

        // Add second set of points (y=55)
        svg.append("g")
            .attr("fill", "none")
            .attr("stroke", color2)
            .attr("stroke-width", 1.5)
            .selectAll("circle")
            .data(d3.range(n))
            .join("circle")
            .attr("cx", (i) => x(z(i)))
            .attr("cy", (i) => y(qy2[i]))
            .attr("r", 3);

        plotHorizontalLine(30, "green", x, y, z);
        plotHorizontalLine(35, "purple", x, y, z);
        plotHorizontalLine(40, "orange", x, y, z);
    }, [width, height, color1, color2, margins]);

    return (
        <div className="w-full p-4 rounded shadow-lg bg-white">
            <svg ref={svgRef} className="w-full h-full"></svg>
        </div>
    );
};

export default QQPlot;
