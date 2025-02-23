import { useEffect, useState } from "react";
import "../App.css";

import ProgramUsageChart from "../components/charts/ProgramUsageChart";

import {
    DailyChromeSummaries,
    DailyProgramSummaries,
    TimelineRows,
} from "../interface/api.interface";

import {
    getChromeSummaries,
    getProgramSummaries,
    getTimelineData,
} from "../api/getData.api";

import ChromeUsageChart from "../components/charts/ChromeUsageChart";
import QQPlotV2 from "../components/charts/QQPlotV2Single";
import { aggregateEvents } from "../util/aggregateEvents";
import { AggregatedTimelineEntry } from "../interface/misc.interface";

function Home() {
    const [programSummaries, setProgramSummaries] =
        useState<DailyProgramSummaries | null>(null);
    const [chromeSummaries, setChromeSummaries] =
        useState<DailyChromeSummaries | null>(null);
    const [timeline, setTimeline] = useState<TimelineRows | null>(null);
    const [reducedMouseEvents, setReducedMouseEvents] = useState<
        AggregatedTimelineEntry[]
    >([]);
    const [reducedKeyboardEvents, setReducedKeyboardEvents] = useState<
        AggregatedTimelineEntry[]
    >([]);

    // const [barsInput, setBarsInput] = useState<BarChartColumn[]>([]);

    // TODO: Chrome time dashboard

    useEffect(() => {
        if (programSummaries == null) {
            //
            getProgramSummaries().then((sums) => {
                // console.log(sums, "44ru");
                setProgramSummaries(sums);
            });
        }
    }, [programSummaries]);

    useEffect(() => {
        if (chromeSummaries == null) {
            getChromeSummaries().then((sums) => {
                // console.log(sums, "58ru");
                setChromeSummaries(sums);
            });
        }
    }, [chromeSummaries]);

    useEffect(() => {
        if (timeline == null) {
            getTimelineData().then((timeline) => {
                setTimeline(timeline);
            });
        }
    }, [timeline]);

    useEffect(() => {
        // reduce timeline rows to avoid CPU hug
        if (timeline) {
            console.log(timeline.mouseRows.length, "74ru");
            const reducedMouseEvents = aggregateEvents(timeline.mouseRows);
            const reducedKeyboardEvents = aggregateEvents(
                timeline.keyboardRows
            );
            setReducedMouseEvents(reducedMouseEvents);
            setReducedKeyboardEvents(reducedKeyboardEvents);
        }
    }, [timeline]);

    // const primaryBg = "#FAFAF9";
    const primaryBlack = "#171717";
    // const accentIndigo = "#6366F1";
    {
        /* // FIXME: programUsageChart re-renders like 5x */
    }

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
                    <h2>
                        Keyboard & Mouse:
                        {timeline ? (
                            `${timeline.keyboardRows.length}, ${timeline?.mouseRows.length}`
                        ) : (
                            <p>Loading</p>
                        )}
                    </h2>
                    {timeline !== null ? (
                        // <TimelineWrapper
                        //     typingSessionLogsInput={timeline?.keyboardRows}
                        //     mouseLogsInput={timeline?.mouseRows}
                        // />
                        <QQPlotV2
                            mouseEvents={reducedMouseEvents}
                            keyboardEvents={reducedKeyboardEvents}
                        />
                    ) : (
                        <p>Loading...</p>
                    )}
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
                    {programSummaries ? (
                        <ProgramUsageChart barsInput={programSummaries} />
                    ) : (
                        <p>Loading...</p>
                    )}
                </div>

                {/* <div>
                    <h2>
                        Keyboard & Mouse:
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
                </div> */}

                {/* // TODO: A Chrome tabs tracker */}
            </div>
        </>
    );
}

export default Home;
