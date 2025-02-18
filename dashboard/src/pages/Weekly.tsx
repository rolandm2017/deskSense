import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import "../App.css";

import {
    getWeeklyChromeUsage,
    getWeeklyProgramUsage,
    getTimelineWeekly,
    getTimelineForWeek,
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
import {
    getUpcomingSaturday,
    convertStringToDate,
    getPreviousSunday,
    getSaturdayThatEndsTheWeek,
    getSundayOfNextWeek,
    formatDate,
    formatDateMmDdYyyy,
    parseDateMmDdYyyy,
} from "../util/timeTools";

function Weekly() {
    const [chrome, setChrome] = useState<WeeklyChromeUsage | null>(null);
    const [programs, setPrograms] = useState<WeeklyProgramUsage | null>(null);

    // const [typing, setTyping] = useState<WeeklyTyping | null>(null);
    // const [clicking, setClicking] = useState<WeeklyClicking | null>(null);
    const [rawTimeline, setRawTimeline] = useState<WeeklyTimeline | null>(null);
    const [aggregatedTimeline, setAggregatedTimeline] =
        useState<WeeklyTimelineAggregate | null>(null);

    const [startDate, setStartDate] = useState<Date | null>(null);
    const [endDate, setEndDate] = useState<Date | null>(null);

    const [nextWeekAvailable, setNextWeekAvailable] = useState(true);

    const [searchParams, setSearchParams] = useSearchParams();

    useEffect(() => {
        const urlParam = searchParams.get("date"); // returns "5432"
        if (urlParam) {
            /* Use this URL param data to set the Showing dates */
            const previousSunday = convertStringToDate(urlParam);
            const upcomingSaturday = getSaturdayThatEndsTheWeek(urlParam);
            setStartDate(previousSunday);
            setEndDate(upcomingSaturday);
            return;
        }
        if (startDate === null || endDate === null) {
            console.log("Getting dates for .... what is this");
            const previousSunday = getPreviousSunday();
            const upcomingSaturday = getUpcomingSaturday();
            setStartDate(previousSunday);
            setEndDate(upcomingSaturday);
        }
    }, [searchParams]);

    useEffect(() => {
        const urlParam = searchParams.get("date"); // returns "5432"
        if (urlParam) {
            /* Load data for refreshes on prior weeks. */
            console.log(urlParam, "68ru");
            getTimelineForWeek(new Date(urlParam)).then((weekly) => {
                console.log(weekly, "71ru");
                // TODO: Get the start and end date
                // Do I make
                setRawTimeline(weekly);
            });
            return;
        }

        getWeeklyChromeUsage().then((weekly) => {
            setChrome(weekly);
        });
        getWeeklyProgramUsage().then((weekly) => {
            setPrograms(weekly);
        });
        getTimelineWeekly().then((weekly) => {
            // TODO: Get the start and end date
            // Do I make
            setRawTimeline(weekly);
        });
    }, []);

    useEffect(() => {
        /* Aggregation */
        if (rawTimeline && aggregatedTimeline === null) {
            const days: DaysOfAggregatedRows[] = [];
            for (const day of rawTimeline.days) {
                const dayClicks = day.row.mouseRows;
                const dayTyping = day.row.keyboardRows;
                const row: DaysOfAggregatedRows = {
                    date: day.date,
                    mouseRow: aggregateEvents(dayClicks),
                    keyboardRow: aggregateEvents(dayTyping),
                };
                days.push(row);
            }
            console.log(
                rawTimeline.days.length,
                aggregatedTimeline,
                days.length,
                "128ru"
            );
            setAggregatedTimeline({ days });
        }
    }, [rawTimeline, aggregatedTimeline]);

    // TODO: Aggregate the mouse and keyboard

    useEffect(() => {
        if (!chrome && !programs) {
            return;
        }
        console.log(chrome);
        console.log(programs);
    }, [chrome, programs]);

    function updateUrlParam(newDate: Date) {
        const input = formatDateMmDdYyyy(newDate);
        setSearchParams({ date: input });
    }

    function dumpOldData() {
        setAggregatedTimeline(null);
        setRawTimeline(null);
    }

    function goToPreviousWeek() {
        if (startDate === null || endDate == null) {
            return;
        }

        dumpOldData();

        const current = new Date(startDate);
        current.setDate(current.getDate() - 7); // Subtract 7 days
        const prevWeekStart = current;
        console.log(prevWeekStart, "being set 135ru");
        setStartDate(prevWeekStart);

        updateUrlParam(prevWeekStart);

        const currentEnd = new Date(endDate);
        currentEnd.setDate(currentEnd.getDate() - 7);
        const prevWeekEnd = currentEnd; // Modified
        console.log(prevWeekEnd, "143ru");
        setEndDate(prevWeekEnd);

        // Do netwoek requests
        console.log("prev wk: allegedly loading data 152ru");
        loadDataForWeek(prevWeekStart);
    }

    function loadDataForWeek(weekStart: Date) {
        setAggregatedTimeline(null); // clear old data
        // FIXME: data loads wrong; a mismatch between the weeks ??
        getTimelineForWeek(weekStart).then((weekly) => {
            console.log("loading weekly 160ru");
            setRawTimeline(weekly);
        });
    }

    function goToNextWeek() {
        if (startDate) {
            const nextSunday: Date = getSundayOfNextWeek(startDate); // startDate is a Sunday
            const concludingSaturday = getSaturdayThatEndsTheWeek(nextSunday);
            dumpOldData();
            setStartDate(nextSunday);
            setEndDate(concludingSaturday);
            updateUrlParam(nextSunday);
            console.log("allegedly loading data 170ru");
            loadDataForWeek(nextSunday); // TODO
        } else {
            console.log("No start date found");
        }
    }

    // FIXME: the the, the date is wrong. ?date=02-09-2025 shows " Feb 16 to Feb 22"

    return (
        <>
            <div>
                <h2>Weekly Reports</h2>
                <div>
                    {/* <h3>Current Week</h3> */}
                    <h3>
                        {startDate && endDate ? (
                            <p>
                                Showing {formatDate(startDate)} to{" "}
                                {formatDate(endDate)}
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
                    <button
                        onClick={() => {
                            // TODO: If there is no previous week available, grey out the button

                            goToPreviousWeek();
                        }}
                    >
                        Previous
                    </button>
                    <button
                        onClick={() => {
                            if (nextWeekAvailable) {
                                // FIXME: Go To Next Week fails: Data is not cycled out
                                goToNextWeek();
                            }
                        }}
                    >
                        Next
                    </button>
                </div>
            </div>
        </>
    );
}

export default Weekly;
