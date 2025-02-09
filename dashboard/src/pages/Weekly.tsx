import { useEffect, useState } from "react";
import "../App.css";

import {
    getWeeklyChromeUsage,
    getWeeklyProgramUsage,
    getTimelineWeekly,
} from "../api/getData.api";
import {
    WeeklyChromeUsage,
    WeeklyProgramUsage,
    WeeklyTimeline,
} from "../interface/weekly.interface";
import QQPlotV2 from "../components/charts/QQPlotV2";
import {
    DaysOfAggregatedRows,
    WeeklyTimelineAggregate,
} from "../interface/misc.interface";
import { aggregateEvents } from "../util/aggregateEvents";

function Weekly() {
    const [chrome, setChrome] = useState<WeeklyChromeUsage | null>(null);
    const [programs, setPrograms] = useState<WeeklyProgramUsage | null>(null);

    // const [typing, setTyping] = useState<WeeklyTyping | null>(null);
    // const [clicking, setClicking] = useState<WeeklyClicking | null>(null);
    const [timeline, setTimeline] = useState<WeeklyTimeline | null>(null);
    const [aggregatedTimeline, setAggregated] =
        useState<WeeklyTimelineAggregate | null>(null);

    const [startDate, setStartDate] = useState<Date | null>(null);
    const [endDate, setEndDate] = useState<Date | null>(null);

    useEffect(() => {
        getWeeklyChromeUsage().then((weekly) => {
            setChrome(weekly);
        });
        getWeeklyProgramUsage().then((weekly) => {
            setPrograms(weekly);
        });
        getTimelineWeekly().then((weekly) => {
            // TODO: Get the start and end date
            // Do I make
            setTimeline(weekly);
        });
    }, []);

    useEffect(() => {
        if (timeline) {
            const days: DaysOfAggregatedRows[] = [];
            for (const day of timeline.days) {
                const dayClicks = day.row.mouseRows;
                const dayTyping = day.row.keyboardRows;
                const row: DaysOfAggregatedRows = {
                    date: day.date,
                    mouseRow: aggregateEvents(dayClicks),
                    keyboardRow: aggregateEvents(dayTyping),
                };
                days.push(row);
            }
            setAggregated({ days });
        }
    }, [timeline]);

    // TODO: Aggregate the mouse and keyboard

    useEffect(() => {
        if (!chrome && !programs) {
            return;
        }
        console.log(chrome);
        console.log(programs);
    }, [chrome, programs]);

    return (
        <>
            <div>
                <h2>Weekly Reports</h2>
                <div>
                    {/* <h3>Current Week</h3> */}
                    <h3>
                        {startDate && endDate ? (
                            <p>
                                Showing {startDate.toString()} to{" "}
                                {endDate.toString()}
                            </p>
                        ) : (
                            <p>Loading</p>
                        )}
                    </h3>
                    {/* // TODO: Show the DATES being displayed, the range. */}
                    {/* // "Showing Sunday 22 to ..." */}
                    <QQPlotV2
                        days={aggregatedTimeline ? aggregatedTimeline.days : []}
                    />
                </div>
                <div>
                    <button>Previous</button>
                    <button>Next</button>
                </div>
            </div>
        </>
    );
}

export default Weekly;
