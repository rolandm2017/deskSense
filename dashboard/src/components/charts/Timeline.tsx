import React, { useEffect, useRef, useState, useMemo } from "react";
import { Timeline, DataSet } from "vis-timeline/standalone";
import "vis-timeline/styles/vis-timeline-graph2d.min.css";
import { MouseLog, TypingSessionLog } from "../../interface/api.interface";
import { TimelineEntrySchema } from "../../api/getData.api";

interface TimelineWrapperProps {
    mouseLogsInput: TimelineEntrySchema[];
    typingSessionLogsInput: TimelineEntrySchema[];
}

// FIXME: many many duplicates here
// 648
// {id: 'mouse-1032', group: 'mouse', content: 'Mouse Event 1032', start: '2025-01-22T07:39:16.739955', end: '2025-01-22T07:39:17.642895'}
// 649
// {id: 'mouse-1032', group: 'mouse', content: 'Mouse Event 1032', start: '2025-01-22T07:39:17.843819', end: '2025-01-22T07:39:18.045050'}
// 650
// {id: 'mouse-1032', group: 'mouse', content: 'Mouse Event 1032', start: '2025-01-22T07:39:18.447073', end: '2025-01-22T07:39:18.547302'}
// 651
// {id: 'mouse-1036', group: 'mouse', content: 'Mouse Event 1036', start: '2025-01-22T07:39:19.552906', end: '2025-01-22T07:39:19.653294'}
// 652
// {id: 'mouse-1036', group: 'mouse', content: 'Mouse Event 1036', start: '2025-01-22T07:39:20.357324', end: '2025-01-22T07:39:20.457870'}


const TimelineWrapper: React.FC<TimelineWrapperProps> = ({
    mouseLogsInput,
    typingSessionLogsInput,
}) => {

    useEffect(() => {
        const v = mouseLogsInput.map((i) => i.)
    })
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
        // let index = 0;

        // // Batch process mouse logs
        // if (mouseLogsInput?.length) {
        //     for (let i = 0; i < mouseLogsInput.length; i++) {
        //         const log = mouseLogsInput[i];
        //         // items[index++] = {
        //         //     id: `mouse-${log.mouseEventId}`,
        //         //     group: "mouse",
        //         //     content: `Mouse Event ${log.mouseEventId}`,
        //         //     start: log.startTime,
        //         //     end: log.endTime,
        //         // };
        //     }
        // }

        // // Batch process typing logs
        // if (typingSessionLogsInput?.length) {
        //     for (let i = 0; i < typingSessionLogsInput.length; i++) {
        //         const log = typingSessionLogsInput[i];
        //         // items[index++] = {
        //         //     id: `keyboard-${log.keyboardEventId}`,
        //         //     group: "keyboard",
        //         //     content: `Typing Session ${log.keyboardEventId}`,
        //         //     start: log.startTime,
        //         //     end: log.endTime,
        //         // };
        //     }
        // }

        return new DataSet(items);
    }, [mouseLogsInput, typingSessionLogsInput]);

    console.log("FOO 60ru");

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
            start: "2025-01-19T09:00:00",
            end: "2025-01-19T23:59:00",
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
