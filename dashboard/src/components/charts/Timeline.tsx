import React, { useEffect, useRef } from "react";
// import { DataSet, Timeline } from "vis-timeline";
import { Timeline, DataSet } from "vis-timeline/standalone";
import "vis-timeline/styles/vis-timeline-graph2d.min.css";

const TimelineWrapper = () => {
    const timelineRef = useRef(null); // Reference for the timeline container

    useEffect(() => {
        const container = timelineRef.current;
        if (container) {
            // const timeline = new Timeline(container, items, groups, options);

            // Define the items (events)
            const items = new DataSet([
                // Mouse Events
                {
                    id: 1,
                    group: "mouse",
                    content: "Mouse Click 1",
                    start: "2025-01-19T09:15:00",
                    end: "2025-01-19T09:45:00",
                },
                {
                    id: 2,
                    group: "mouse",
                    content: "Mouse Move",
                    start: "2025-01-19T10:00:00",
                    end: "2025-01-19T10:30:00",
                },
                {
                    id: 3,
                    group: "mouse",
                    content: "Mouse Drag",
                    start: "2025-01-19T11:00:00",
                    end: "2025-01-19T11:30:00",
                },

                // Keyboard Events
                {
                    id: 4,
                    group: "keyboard",
                    content: "Key Press A",
                    start: "2025-01-19T12:00:00",
                    end: "2025-01-19T12:20:00",
                },
                {
                    id: 5,
                    group: "keyboard",
                    content: "Key Press B",
                    start: "2025-01-19T13:15:00",
                    end: "2025-01-19T13:45:00",
                },
                {
                    id: 6,
                    group: "keyboard",
                    content: "Key Combo",
                    start: "2025-01-19T15:30:00",
                    end: "2025-01-19T16:00:00",
                },
            ]);

            // Define the groups (rows)
            const groups = new DataSet([
                { id: "mouse", content: "Mouse Events" },
                { id: "keyboard", content: "Keyboard Events" },
            ]);

            // Define timeline options
            const options = {
                start: "2025-01-19T09:00:00",
                end: "2025-01-19T23:59:00",
                stack: false,
                margin: { item: 10 },
                zoomable: true,
                orientation: "top",
            };

            // Create the timeline
            const timeline = new Timeline(container, items, groups, options);

            // Add interactivity: handle clicks
            timeline.on("click", (props) => {
                if (props.item) {
                    alert(`You clicked on event with ID: ${props.item}`);
                } else {
                    console.log("Clicked on empty space");
                }
            });

            // Cleanup on component unmount
            return () => timeline.destroy();
        }
    }, [timelineRef.current]);

    return (
        <div
            ref={timelineRef}
            style={{ height: "400px", border: "1px solid lightgray" }}
        />
    );
};

export default TimelineWrapper;
