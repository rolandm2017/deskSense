import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import "../App.css";

import {
    getWeeklyChromeUsage,
    getWeeklyProgramUsage,
    getEnhancedChromeUsageForPastWeek,
    getTimelineForCurrentWeek,
    getTimelineForPastWeek,
} from "../api/getData.api";
import {
    DayOfChromeUsage,
    SocialMediaUsage,
    WeeklyBreakdown,
    WeeklyChromeUsage,
    WeeklyProgramUsage,
    WeeklyTimeline,
} from "../interface/weekly.interface";

import { BarChartDayData } from "../interface/misc.interface";
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
import WeeklyUsageChart from "../components/charts/WeeklyBarChart";

function Weekly() {
    const [chrome, setChrome] = useState<WeeklyChromeUsage | null>(null);
    const [programs, setPrograms] = useState<WeeklyProgramUsage | null>(null);

    const [rawTimeline, setRawTimeline] = useState<WeeklyTimeline | null>(null);
    const [aggregatedTimeline, setAggregatedTimeline] =
        useState<WeeklyTimelineAggregate | null>(null);

    const [startDate, setStartDate] = useState<Date | null>(null);
    const [endDate, setEndDate] = useState<Date | null>(null);

    const [nextWeekAvailable, setNextWeekAvailable] = useState(true);

    const [weeklyBreakdown, setWeeklyBreakdown] =
        useState<WeeklyBreakdown | null>(null);

    const [socialMediaUsage, setSocialMediaUsage] = useState<
        SocialMediaUsage[] | null
    >(null);

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
            const asDate = new Date(urlParam);
            /* Load data for refreshes on prior weeks. */
            console.log(urlParam, "68ru");
            loadDataForWeek(asDate);
            return;
        }

        getWeeklyChromeUsage().then((weekly: WeeklyChromeUsage) => {
            // TODO: Move this into the api as a layer
            const withConvertedDateObjs: DayOfChromeUsage[] = weekly.days.map(
                (day) => {
                    return {
                        date: new Date(day.date),
                        content: day.content,
                    };
                }
            );
            const withFixedDates: WeeklyChromeUsage = {
                days: withConvertedDateObjs,
            };
            setChrome(withFixedDates);
        });
        getWeeklyProgramUsage().then((weekly: WeeklyProgramUsage) => {
            // TODO: Convert date string to new Date() like up above
            setPrograms(weekly);
        });
        getTimelineForCurrentWeek().then((weekly) => {
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

            setAggregatedTimeline({ days });
        }
    }, [rawTimeline, aggregatedTimeline]);

    // TODO: Aggregate the mouse and keyboard

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
        setStartDate(prevWeekStart);

        updateUrlParam(prevWeekStart);

        const currentEnd = new Date(endDate);
        currentEnd.setDate(currentEnd.getDate() - 7);
        const prevWeekEnd = currentEnd; // Modified
        setEndDate(prevWeekEnd);

        // Do netwoek requests
        loadDataForWeek(prevWeekStart);
    }

    function loadDataForWeek(weekStart: Date) {
        getEnhancedChromeUsageForPastWeek(weekStart).then((chrome) => {
            setChrome(chrome);
        });
        // FIXME: data loads wrong; a mismatch between the weeks ??
        getTimelineForPastWeek(weekStart).then((weekly) => {
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
            loadDataForWeek(nextSunday);
        } else {
            console.log("No start date found");
        }
    }

    function convertToTwitterOnlyData(
        weekOfUsage: WeeklyChromeUsage
    ): BarChartDayData[] {
        // find twitter
        return weekOfUsage.days.map((day) => {
            // Find Twitter usage in the columns array
            const twitterUsage = day.content.columns.find(
                (column) =>
                    column.domainName === "x.com" ||
                    column.domainName === "twitter.com"
            );

            return {
                day: day.date,
                hoursSpent: twitterUsage ? twitterUsage.hoursSpent : 0,
            };
        });
    }

    return (
        <>
            <div>
                <h2 className="text-3xl my-2">Weekly Reports</h2>

                <div>
                    <h3>Twitter Usage</h3>
                    <h3 className="text-xl">
                        {startDate && endDate ? (
                            <p className="mt-4">
                                Showing {formatDate(startDate)} to{" "}
                                {formatDate(endDate)}
                            </p>
                        ) : (
                            <p>Loading</p>
                        )}
                    </h3>
                    {
                        chrome ? (
                            <WeeklyUsageChart
                                title={"Overview"}
                                data={convertToTwitterOnlyData(chrome)}
                            />
                        ) : null // null
                    }
                </div>
                <div className="mt-4 ">
                    <button
                        className="mr-2 shadow-lg bg-blue-100"
                        onClick={() => {
                            // TODO: If there is no previous week available, grey out the button

                            goToPreviousWeek();
                        }}
                    >
                        Previous
                    </button>
                    <button
                        className="shadow-lg bg-blue-100"
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

                <div>
                    <h3>Twitter Usage</h3>
                    <h3 className="text-xl">
                        {startDate && endDate ? (
                            <p className="mt-4">
                                Showing {formatDate(startDate)} to{" "}
                                {formatDate(endDate)}
                            </p>
                        ) : (
                            <p>Loading</p>
                        )}
                    </h3>
                    {
                        chrome ? (
                            <WeeklyUsageChart
                                title={"Twitter"}
                                data={convertToTwitterOnlyData(chrome)}
                            />
                        ) : null // null
                    }
                </div>
                <div className="mt-4 ">
                    <button
                        className="mr-2 shadow-lg bg-blue-100"
                        onClick={() => {
                            // TODO: If there is no previous week available, grey out the button

                            goToPreviousWeek();
                        }}
                    >
                        Previous
                    </button>
                    <button
                        className="shadow-lg bg-blue-100"
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
                <div>
                    {/* <h3>Current Week</h3> */}
                    <h3 className="text-xl">
                        {startDate && endDate ? (
                            <p className="mt-4">
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

                <div className="mt-4 ">
                    <button
                        className="mr-2 shadow-lg bg-blue-100"
                        onClick={() => {
                            // TODO: If there is no previous week available, grey out the button

                            goToPreviousWeek();
                        }}
                    >
                        Previous
                    </button>
                    <button
                        className="shadow-lg bg-blue-100"
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
