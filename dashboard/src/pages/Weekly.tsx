import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import "../App.css";

import {
    getPresentWeekProgramUsage,
    getPresentWeekChromeUsage,
    getEnhancedChromeUsageForPastWeek,
    getTimelineForPresentWeek,
    getTimelineForPastWeek,
    getEnhancedWeeklyBreakdown,
} from "../api/getData.api";
import {
    DayOfChromeUsage,
    DayOfTimelineRows,
    PartiallyAggregatedWeeklyTimeline,
    SocialMediaUsage,
    WeeklyBreakdown,
    WeeklyChromeUsage,
    WeeklyProgramUsage,
    WeeklyTimeline,
} from "../interface/weekly.interface";

import { BarChartDayData } from "../interface/misc.interface";
import PeripheralsChart from "../components/charts/PeripheralsChart";
import {
    DayOfAggregatedRows,
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
} from "../util/timeTools";
import WeeklyUsageChart from "../components/charts/WeeklyBarChart";
import StackedBarChart from "../components/charts/StackedBarChart";
import NavigationButtons from "../components/NavigationButtons";
import StartEndDateDisplay from "../components/StartEndDateDisplay";

// ### ###
// ### ### ###
// ### ### ### ###
// ## Semantic Distinctions
// "Present Week" → Always refers to the real-world, system-clock-defined week (i.e., today’s calendar week).
// "Viewed Week" → Refers to the week the user is currently viewing on the dashboard.
// "Loaded Week" → The week whose data is currently loaded in state (useful internally).
// ### ### ### ###
// ### ### ###
// ### ###

function Weekly() {
    const [chrome, setChrome] = useState<WeeklyChromeUsage | null>(null);
    const [programs, setPrograms] = useState<WeeklyProgramUsage | null>(null);

    // FIXME: why is there three?

    const [prevWeeksRawTimeline, setPrevWeeksRawTimeline] =
        useState<WeeklyTimeline | null>(null);

    const [aggregatedTimeline, setAggregatedTimeline] =
        useState<WeeklyTimelineAggregate | null>(null);

    const [presentWeekRawTimeline, setPresentWeekRawTimeline] =
        useState<PartiallyAggregatedWeeklyTimeline | null>(null);

    const [startDate, setStartDate] = useState<Date | null>(null);
    const [endDate, setEndDate] = useState<Date | null>(null);

    const [nextWeekAvailable, setNextWeekAvailable] = useState(true);

    const [weeklyBreakdown, setWeeklyBreakdown] =
        useState<WeeklyBreakdown | null>(null);

    const [searchParams, setSearchParams] = useSearchParams();

    useEffect(() => {
        /* Handle setting dates display */
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
        /* Load current week's data */

        getPresentWeekProgramUsage().then((weekly: WeeklyProgramUsage) => {
            // TODO: Convert date string to new Date() like up above
            setPrograms(weekly);
        });
        getPresentWeekChromeUsage().then((weekly: WeeklyChromeUsage) => {
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

        getTimelineForPresentWeek().then((weekly) => {
            setPresentWeekRawTimeline(weekly);
            // TODO: follow downstream logic and set either currentWeek or PrevWeek depending on which is which
        });
    }, []);

    useEffect(() => {
        /* Aggregation for previous weeks */
        if (prevWeeksRawTimeline && aggregatedTimeline === null) {
            const days: DayOfAggregatedRows[] = [];
            for (const day of prevWeeksRawTimeline.days) {
                const dayClicks = day.row.mouseRows;
                const dayTyping = day.row.keyboardRows;
                const row: DayOfAggregatedRows = {
                    date: day.date,
                    mouseRow: aggregateEvents(dayClicks),
                    keyboardRow: aggregateEvents(dayTyping),
                };
                days.push(row);
            }

            setAggregatedTimeline({ days });
        }
    }, [prevWeeksRawTimeline, aggregatedTimeline]);

    useEffect(() => {
        /* Aggregation */
        if (presentWeekRawTimeline && aggregatedTimeline === null) {
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

            days.forEach((obj, index) => {
                console.log(`Object ${index} keys:`, Object.keys(obj));
            });

            setAggregatedTimeline({ days });
        }
    }, [presentWeekRawTimeline, aggregatedTimeline]);

    function updateUrlParam(newDate: Date) {
        const input = formatDateMmDdYyyy(newDate);
        setSearchParams({ date: input });
    }

    function dumpOldData() {
        setAggregatedTimeline(null);
        setPrevWeeksRawTimeline(null);
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
            setPrevWeeksRawTimeline(weekly);
        });
        getEnhancedWeeklyBreakdown(weekStart).then(
            (breakdown: WeeklyBreakdown) => {
                setWeeklyBreakdown(breakdown);
            }
        );
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
                    <h3 className="text-2xl">Overview</h3>
                    <StartEndDateDisplay
                        startDate={startDate}
                        endDate={endDate}
                    />
                    {weeklyBreakdown ? (
                        <StackedBarChart
                            title={""}
                            data={weeklyBreakdown.days}
                        />
                    ) : null}
                </div>
                <NavigationButtons
                    nextWeekAvailable={nextWeekAvailable}
                    goToPreviousWeek={goToPreviousWeek}
                    goToNextWeek={goToNextWeek}
                />

                <div>
                    <h3 className="mt-4 text-2xl">Twitter Usage</h3>
                    <StartEndDateDisplay
                        startDate={startDate}
                        endDate={endDate}
                    />
                    {
                        chrome ? (
                            <WeeklyUsageChart
                                title={""}
                                data={convertToTwitterOnlyData(chrome)}
                            />
                        ) : null // null
                    }
                </div>
                <NavigationButtons
                    nextWeekAvailable={nextWeekAvailable}
                    goToPreviousWeek={goToPreviousWeek}
                    goToNextWeek={goToNextWeek}
                />
                <div>
                    <h3 className="mt-4 text-2xl">Keyboard & Mouse Usage</h3>

                    <StartEndDateDisplay
                        startDate={startDate}
                        endDate={endDate}
                    />
                    {/* // TODO: Show the DATES being displayed, the range. */}
                    {/* // "Showing Sunday 22 to ..." */}
                    <PeripheralsChart
                        days={aggregatedTimeline ? aggregatedTimeline.days : []}
                    />
                </div>

                <NavigationButtons
                    nextWeekAvailable={nextWeekAvailable}
                    goToPreviousWeek={goToPreviousWeek}
                    goToNextWeek={goToNextWeek}
                />
            </div>
        </>
    );
}

export default Weekly;
