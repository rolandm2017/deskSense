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

    // TODO: Chrome time dashboard

    const hours = 36000000; // 1000 * 60 * 60

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

    const primaryBg = "#FAFAF9";
    const primaryBlack = "#171717";
    const accentIndigo = "#6366F1";

    return (
        <>
            <div>
                <div>
                    <h1
                        style={{
                            color: primaryBlack,
                            fontSize: "28px",
                            border: "2px solid black",
                        }}
                    >
                        DeskSense Dashboard
                    </h1>
                </div>
                <div style={{ border: "5px solid black", margin: "0px" }}>
                    <h2 style={{ margin: "0px" }}>
                        Programs {programReport?.count.toString()}
                    </h2>
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

                {/* // TODO: A Chrome tabs tracker */}
            </div>
        </>
    );
}

export default App;
