import { useEffect, useState } from "react";
import "../App.css";

// import ProgramUsageChart from "../components/charts/ProgramUsageChart";

import {
    DailyChromeSummaries,
    DailyProgramSummaries,
} from "../interface/api.interface";

import {
    getChromeSummaries,
    getPresentWeekProgramTimeline,
    getProgramSummaries,
    getTimelineForPresentWeek,
} from "../api/getData.api";

// import ChromeUsageChart from "../components/charts/ChromeUsageChart";
import PeripheralsTimeline from "../components/charts/PeripheralsTimeline";
import { aggregateEvents } from "../util/aggregateEvents";
import { DayOfAggregatedRows } from "../interface/misc.interface";
import {
    DayOfTimelineRows,
    PartiallyAggregatedWeeklyTimeline,
    WeeklyProgramTimelines,
} from "../interface/weekly.interface";
import ProgramTimeline from "../components/charts/ProgramTimeline";

function Home() {
    const [programSummaries, setProgramSummaries] =
        useState<DailyProgramSummaries | null>(null);
    const [chromeSummaries, setChromeSummaries] =
        useState<DailyChromeSummaries | null>(null);
    // const [timeline, setTimeline] = useState<TimelineRows | null>(null);

    const [programTimelines, setProgramTimelines] =
        useState<WeeklyProgramTimelines | null>(null);

    // const [aggregatedTimeline, setAggregatedTimeline] =
    // useState<WeeklyTimelineAggregate | null>(null);

    const [presentWeekRawTimeline, setRawTimeline] =
        useState<PartiallyAggregatedWeeklyTimeline | null>(null);

    const [aggregatedDays, setAggregatedDays] = useState<
        DayOfAggregatedRows[] | null
    >(null);

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
        if (presentWeekRawTimeline === null) {
            getTimelineForPresentWeek().then((weekly) => {
                // TODO: Get the start and end date
                // Do I make
                console.log(weekly, "72ru");
                setRawTimeline(weekly);
            });
        }
    }, [presentWeekRawTimeline]);

    useEffect(() => {
        if (programTimelines === null) {
            getPresentWeekProgramTimeline().then((timelines) => {
                setProgramTimelines(timelines);
            });
        }
    }, [programTimelines]);

    useEffect(() => {
        /* Aggregation */
        console.log(presentWeekRawTimeline, aggregatedDays, "80ru");
        if (presentWeekRawTimeline && aggregatedDays === null) {
            const days: DayOfAggregatedRows[] = [];
            // FIXME: Days before today are already aggregated on server
            // FIXME: so you don't need to repeat it here. You really don't. It's an interface problem.
            console.log(presentWeekRawTimeline, "95ru");
            // FIXME: comes back as 7 days
            const today: DayOfTimelineRows = presentWeekRawTimeline.today;
            console.log(today, "96ru");

            // Aggregate today:
            const dayClicks = today.row.mouseRows;
            const dayTyping = today.row.keyboardRows;
            const row: DayOfAggregatedRows = {
                date: today.date,
                mouseRow: aggregateEvents(dayClicks),
                keyboardRow: aggregateEvents(dayTyping),
            };
            const convertedIntoAggregations: DayOfAggregatedRows[] =
                presentWeekRawTimeline.beforeToday.map((day) => {
                    return {
                        date: day.date,
                        mouseRow: day.row.mouseRows,
                        keyboardRow: day.row.keyboardRows,
                    };
                });

            console.log(convertedIntoAggregations);
            days.push(...convertedIntoAggregations);
            days.push(row);

            // days.forEach((obj, index) => {
            //     console.log(`Object ${index} keys:`, Object.keys(obj));
            // });

            // const temp = days[6];

            // console.log(temp, "temp temp 117ru");

            // setAggregatedDays([temp]);
            setAggregatedDays(days);
        }
    }, [presentWeekRawTimeline, aggregatedDays]);

    // useEffect(() => {
    //     if (timeline == null) {
    //         getTodaysTimelineData().then((timeline) => {
    //             // TODO: change endpoint to serve it up by day
    //             setTimeline(timeline);
    //         });
    //     }
    // }, [timeline]);

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
                    <h2>Keyboard & Mouse</h2>
                    {/* // TODO: Use Weekly Peripherals chart on Home */}
                    {aggregatedDays !== null ? (
                        <PeripheralsTimeline days={aggregatedDays} />
                    ) : (
                        <p>Loading...</p>
                    )}
                </div>
                <div>
                    <h2>Program Timelines</h2>
                    {programTimelines !== null ? (
                        <ProgramTimeline days={programTimelines.days} />
                    ) : (
                        <p>Loading...</p>
                    )}
                </div>
                <div>
                    <h2 style={{ margin: "0px" }}>Chrome</h2>
                    {chromeSummaries ? (
                        // <ChromeUsageChart barsInput={chromeSummaries} />
                        <p>foo</p>
                    ) : (
                        <p>Loading...</p>
                    )}
                </div>
                <div style={{ border: "5px solid black", margin: "0px" }}>
                    <h2 style={{ margin: "0px" }}>
                        Programs {programSummaries?.columns.length}
                    </h2>
                    {programSummaries ? (
                        // <ProgramUsageChart barsInput={programSummaries} />
                        <p>bar</p>
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
