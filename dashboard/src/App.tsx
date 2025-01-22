import { useEffect, useState } from "react";
import "./App.css";

import ProgramUsageChart from "./components/charts/ProgramUsageChart";

import {
    DailyProgramSummaries,
    getKeyboardReport,
    getMouseReport,
    getProgramReport,
    getProgramSummaries,
    getTimelineData,
    TimelineRows,
} from "./api/getData.api";
import { BarChartColumn } from "./interface/misc.interface";
import {
    TypingSessionsReport,
    MouseReport,
    ProgramActivityLog,
    ProgramActivityReport,
} from "./interface/api.interface";
import TimelineWrapper from "./components/charts/Timeline";

function App() {
    const [typingReport, setTypingReport] = useState<TypingSessionsReport | null>(null) // prettier-ignore
    const [mouseReport, setMouseReport] = useState<MouseReport | null>(null) // prettier-ignore
    const [programReport, setProgramReport] = useState<ProgramActivityReport | null>(null); // prettier-ignore

    const [summaries, setSummaries] = useState<DailyProgramSummaries | null>(
        null
    );
    const [timeline, setTimeline] = useState<TimelineRows | null>(null);

    // const [barsInput, setBarsInput] = useState<BarChartColumn[]>([]);

    const hours = 36000000; // 1000 * 60 * 60

    // function processTimeReports(
    //     reports: ProgramActivityLog[]
    // ): BarChartColumn[] {
    //     // Create a hashtable to store total time per window
    //     const windowTimes: { [key: string]: number } = {};

    //     // Calculate time differences and aggregate
    //     reports.forEach((report: ProgramActivityLog) => {
    //         const startTime = new Date(report.startTime);
    //         const endTime = new Date(report.endTime);
    //         const durationInHours =
    //             (endTime.getTime() - startTime.getTime()) / hours; // Convert to hours

    //         if (windowTimes[report.window]) {
    //             windowTimes[report.window] += durationInHours;
    //         } else {
    //             windowTimes[report.window] = durationInHours;
    //         }
    //     });

    //     // Convert to BarChartColumn array and sort by hours spent
    //     const chartData: BarChartColumn[] = Object.entries(windowTimes)
    //         .map(([programName, hoursSpent]) => ({
    //             programName,
    //             hoursSpent: Number(hoursSpent.toFixed(4)), // Round to 4 decimal places
    //         }))
    //         .sort((a, b) => b.hoursSpent - a.hoursSpent);

    //     return chartData;
    // }

    useEffect(() => {
        if (summaries == null) {
            //
            getProgramSummaries().then((sums) => {
                console.log(sums);
                setSummaries(sums);
            });
        }
    }, [summaries]);

    useEffect(() => {
        if (timeline == null) {
            getTimelineData().then((timeline) => {
                console.log(timeline);
                setTimeline(timeline);
            });
        }
    }, [timeline]);

    return (
        <>
            <div>
                <div>
                    <h1>DeskSense Dashboard</h1>
                </div>
                <div style={{ border: "5px solid black" }}>
                    <h2>Programs {programReport?.count.toString()}</h2>
                    {summaries ? (
                        <ProgramUsageChart barsInput={summaries} />
                    ) : (
                        <p>Loading...</p>
                    )}
                </div>
                <div>
                    <h2>
                        Keyboard & Mouse: {typingReport?.count},{" "}
                        {mouseReport?.count}
                    </h2>
                    {timeline !== null ? (
                        <TimelineWrapper
                            typingSessionLogsInput={timeline?.keyboardRows}
                            mouseLogsInput={timeline?.mouseRows}
                        />
                    ) : (
                        <p>Loading...</p>
                    )}
                </div>
            </div>
        </>
    );
}

export default App;
