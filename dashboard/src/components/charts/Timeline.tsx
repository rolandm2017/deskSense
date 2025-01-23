import React, { useEffect, useRef, useMemo } from "react";
import { Timeline, DataSet } from "vis-timeline/standalone";
import "vis-timeline/styles/vis-timeline-graph2d.min.css";
import { TimelineEntrySchema } from "../../api/getData.api";

interface TimelineWrapperProps {
    mouseLogsInput: TimelineEntrySchema[];
    typingSessionLogsInput: TimelineEntrySchema[];
}

const TimelineWrapper: React.FC<TimelineWrapperProps> = ({
    mouseLogsInput,
    typingSessionLogsInput,
}) => {
    console.log(mouseLogsInput.length, typingSessionLogsInput.length, "27ru");
    // Memoize the DataSet creation
    const formattedApiDataDataSet = useMemo(() => {
        if (!mouseLogsInput?.length && !typingSessionLogsInput?.length) {
            return new DataSet([]);
        }
        // Pre-allocate array size for better memory efficiency
        const totalItems =
            (mouseLogsInput?.length || 0) +
            (typingSessionLogsInput?.length || 0);
        const items = [...mouseLogsInput, ...typingSessionLogsInput];

        return new DataSet(items);
    }, [mouseLogsInput, typingSessionLogsInput]);

    // Memoize groups to prevent unnecessary recreations
    const groups = useMemo(
        () =>
            new DataSet([
                { id: "mouse", content: "Mouse Events" },
                { id: "keyboard", content: "Keyboard Events" },
            ]),
        []
    );

    // Memoize options to prevent unnecessary recreations
    const options = useMemo(
        () => ({
            start: "2025-01-19T05:00:00", // Changed from 09:00 to 05:00
            end: "2025-01-19T23:59:59", // Changed from 23:59:00 to 23:59:59
            stack: false,
            margin: { item: 10 },
            zoomable: true,
            orientation: "top",
            // Performance options
            rollingMode: {
                follow: true,
                offset: 0.5,
            },
            verticalScroll: true,
            maxHeight: "100%",
            height: "100%",
            minHeight: "350px",
            onInitialDrawComplete: () => {
                console.log("Timeline initial render complete");
            },
        }),
        []
    );

    const timelineRef = useRef<HTMLDivElement>(null);
    const timelineInstanceRef = useRef<Timeline | null>(null);

    useEffect(() => {
        const container = timelineRef.current;
        if (!container) return;

        // Create timeline instance
        timelineInstanceRef.current = new Timeline(
            container,
            formattedApiDataDataSet,
            groups,
            options
        );

        // Debounced click handler
        let clickTimeout: ReturnType<typeof setTimeout>;
        const handleClick = (props: any) => {
            clearTimeout(clickTimeout);
            clickTimeout = setTimeout(() => {
                if (props.item) {
                    alert(`You clicked on event with ID: ${props.item}`);
                }
            }, 300);
        };

        timelineInstanceRef.current.on("click", handleClick);

        // Cleanup
        return () => {
            clearTimeout(clickTimeout);
            if (timelineInstanceRef.current) {
                timelineInstanceRef.current.destroy();
            }
        };
    }, []);

    // Update data without recreating timeline instance
    useEffect(() => {
        if (timelineInstanceRef.current) {
            timelineInstanceRef.current.setItems(formattedApiDataDataSet);
        }
    }, [formattedApiDataDataSet]);

    return <div ref={timelineRef} className="h-96 border border-gray-200" />;
};

export default TimelineWrapper;
