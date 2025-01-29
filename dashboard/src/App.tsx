import { useEffect, useState } from "react";
import "./App.css";

import ProgramUsageChart from "./components/charts/ProgramUsageChart";

import {
    DailyChromeSummaries,
    DailyProgramSummaries,
    getChromeSummaries,
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
import ChromeUsageChart from "./components/charts/ChromeUsageChart";

function App() {
    const [programSummaries, setProgramSummaries] =
        useState<DailyProgramSummaries | null>(null);
    const [chromeSummaries, setChromeSummaries] =
        useState<DailyChromeSummaries | null>(null);
    const [timeline, setTimeline] = useState<TimelineRows | null>(null);

    // const [barsInput, setBarsInput] = useState<BarChartColumn[]>([]);

    // TODO: Chrome time dashboard

    const hours = 36000000; // 1000 * 60 * 60

    useEffect(() => {
        if (programSummaries == null) {
            //
            getProgramSummaries().then((sums) => {
                console.log(sums, "44ru");
                setProgramSummaries(sums);
            });
        }
    }, [programSummaries]);

    useEffect(() => {
        if (chromeSummaries == null) {
            getChromeSummaries().then((sums) => {
                console.log(sums, "58ru");
                setChromeSummaries(sums);
            });
        }
    }, [chromeSummaries]);

    useEffect(() => {
        if (timeline == null) {
            getTimelineData().then((timeline) => {
                console.log(timeline, "53ru");
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
                <div>
                    <h2 style={{ margin: "0px" }}>Chrome</h2>
                    {chromeSummaries ? (
                        <ChromeUsageChart barsInput={chromeSummaries} />
                    ) : (
                        <p>Loading...</p>
                    )}
                </div>
                <div style={{ border: "5px solid black", margin: "0px" }}>
                    <h2 style={{ margin: "0px" }}>
                        Programs {programSummaries?.columns.length}
                    </h2>
                    {/* // FIXME: programUsageChart re-renders like 5x */}
                    {programSummaries ? (
                        <ProgramUsageChart barsInput={programSummaries} />
                    ) : (
                        <p>Loading...</p>
                    )}
                </div>

                <div>
                    <h2>
                        Keyboard & Mouse:{" "}
                        {timeline ? (
                            `${timeline.keyboardRows.length}, ${timeline?.mouseRows.length}`
                        ) : (
                            <p>Loading</p>
                        )}
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
