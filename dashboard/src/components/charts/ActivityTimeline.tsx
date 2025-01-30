import React, { useState, useRef, WheelEvent } from "react";

interface ActivityEvent {
    type: "keyboard" | "mouse";
    timestamp: Date;
}

interface ViewBox {
    x: number;
    width: number;
}

interface TimeRange {
    startTime: Date;
    endTime: Date;
}

interface ActivityTimelineProps {
    startHour?: number;
    endHour?: number;
    keyboardEventCount?: number;
    mouseEventCount?: number;
    date?: Date;
}

const ActivityTimeline: React.FC<ActivityTimelineProps> = ({
    startHour = 5,
    endHour = 22,
    keyboardEventCount = 100,
    mouseEventCount = 100,
    date = new Date("2025-01-29"),
}) => {
    const [viewBox, setViewBox] = useState<ViewBox>({ x: 0, width: 800 });
    const svgRef = useRef<SVGSVGElement | null>(null);

    // Constants
    const totalWidth = 800;
    const height = 100;
    const padding = 60;

    // Create time range based on props
    const getTimeRange = (): TimeRange => {
        const start = new Date(date);
        start.setHours(startHour, 0, 0, 0);

        const end = new Date(date);
        end.setHours(endHour, 0, 0, 0);

        return {
            startTime: start,
            endTime: end,
        };
    };

    const timeRange = getTimeRange();

    const generateEvents = (
        count: number,
        type: ActivityEvent["type"]
    ): ActivityEvent[] => {
        const events: ActivityEvent[] = [];
        const timeSpan =
            timeRange.endTime.getTime() - timeRange.startTime.getTime();

        for (let i = 0; i < count; i++) {
            const randomTime = new Date(
                timeRange.startTime.getTime() + Math.random() * timeSpan
            );
            events.push({
                type,
                timestamp: randomTime,
            });
        }
        return events.sort(
            (a, b) => a.timestamp.getTime() - b.timestamp.getTime()
        );
    };

    const keyboardEvents = generateEvents(keyboardEventCount, "keyboard");
    const mouseEvents = generateEvents(mouseEventCount, "mouse");

    const getXPosition = (timestamp: Date): number => {
        const position =
            ((timestamp.getTime() - timeRange.startTime.getTime()) /
                (timeRange.endTime.getTime() - timeRange.startTime.getTime())) *
            (totalWidth - 2 * padding);
        return position + padding;
    };

    // Generate hour markers
    const generateHourMarkers = (): Date[] => {
        const markers: Date[] = [];
        for (let hour = startHour; hour <= endHour; hour++) {
            const time = new Date(date);
            time.setHours(hour, 0, 0, 0);
            markers.push(time);
        }
        return markers;
    };

    const hourMarkers = generateHourMarkers();

    const handleWheel = (e: WheelEvent<SVGSVGElement>): void => {
        e.preventDefault();

        if (!svgRef.current) return;

        const svg = svgRef.current;
        const point = svg.createSVGPoint();
        const rect = svg.getBoundingClientRect();

        // Calculate point relative to SVG
        point.x = e.clientX - rect.left;
        const svgPoint = point.matrixTransform(svg.getScreenCTM()?.inverse());

        // Calculate zoom
        const zoomFactor = e.deltaY > 0 ? 1.1 : 0.9;
        const newWidth = Math.min(
            Math.max(viewBox.width * zoomFactor, 100),
            totalWidth
        );

        // Calculate new x position to zoom toward mouse
        const mouseRatio = (svgPoint.x - viewBox.x) / viewBox.width;
        const newX = Math.max(
            0,
            Math.min(svgPoint.x - mouseRatio * newWidth, totalWidth - newWidth)
        );

        setViewBox({
            x: newX,
            width: newWidth,
        });
    };

    // Format hour label with AM/PM
    const formatHourLabel = (hour: number): string => {
        const period = hour >= 12 ? "PM" : "AM";
        const displayHour = hour % 12 || 12;
        return `${displayHour}${period}`;
    };

    return (
        <div className="w-full max-w-4xl p-4">
            <svg
                ref={svgRef}
                viewBox={`${viewBox.x} 0 ${viewBox.width} ${height}`}
                className="w-full h-full"
                onWheel={handleWheel}
            >
                {/* Base line */}
                <line
                    x1={padding}
                    y1={height / 2}
                    x2={totalWidth - padding}
                    y2={height / 2}
                    stroke="#e5e7eb"
                    strokeWidth="1"
                />

                {/* Hour markers */}
                {hourMarkers.map((time, i) => (
                    <g key={`marker-${i}`}>
                        <line
                            x1={getXPosition(time)}
                            y1={height / 2 - 25}
                            x2={getXPosition(time)}
                            y2={height / 2 + 25}
                            stroke="#d2d4d9"
                            strokeWidth="1.3"
                            strokeDasharray="3,2"
                        />
                        <text
                            x={getXPosition(time)}
                            y={height - 5}
                            textAnchor="middle"
                            fontSize="12"
                            className="fill-current"
                        >
                            {formatHourLabel(time.getHours())}
                        </text>
                    </g>
                ))}

                {/* Keyboard events - top line */}
                <g>
                    {keyboardEvents.map((event, i) => (
                        <line
                            key={`k-${i}`}
                            x1={getXPosition(event.timestamp)}
                            y1={height / 2 - 15}
                            x2={getXPosition(event.timestamp)}
                            y2={height / 2 - 5}
                            stroke="#3b82f6"
                            strokeWidth="1.5"
                        />
                    ))}
                </g>

                {/* Mouse events - bottom line */}
                <g>
                    {mouseEvents.map((event, i) => (
                        <line
                            key={`m-${i}`}
                            x1={getXPosition(event.timestamp)}
                            y1={height / 2 + 5}
                            y2={height / 2 + 15}
                            x2={getXPosition(event.timestamp)}
                            stroke="#ef4444"
                            strokeWidth="1.5"
                        />
                    ))}
                </g>
            </svg>

            {/* Legend */}
            <div className="flex gap-4 justify-center mt-2">
                <div className="flex items-center">
                    <div className="w-4 h-0.5 bg-blue-500 mr-2"></div>
                    <span className="text-sm">
                        Keyboard ({keyboardEvents.length} events)
                    </span>
                </div>
                <div className="flex items-center">
                    <div className="w-4 h-0.5 bg-red-500 mr-2"></div>
                    <span className="text-sm">
                        Mouse ({mouseEvents.length} events)
                    </span>
                </div>
            </div>
        </div>
    );
};

export default ActivityTimeline;
