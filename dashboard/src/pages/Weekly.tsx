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

    function getPreviousSunday() {
        let today = new Date();
        let daysSinceSunday = today.getDay(); // Sunday is 0
        let previousSunday = new Date(today);
        previousSunday.setDate(today.getDate() - daysSinceSunday);
        return previousSunday; // TODO: Test this function
    }

    function getUpcomingSaturday() {
        let today = new Date();
        let daysUntilSaturday = 6 - today.getDay(); // Saturday is 6
        let nextSaturday = new Date(today);
        nextSaturday.setDate(today.getDate() + daysUntilSaturday);
        return nextSaturday;
    }

    function convertStringToDate(someSundayAsString: string) {
        return new Date(someSundayAsString);
    }

    function getSaturdayThatEndsTheWeek(someSundayAsString: string) {
        const someSunday = new Date(someSundayAsString);
        let saturdayDate = new Date(someSunday);
        saturdayDate.setDate(someSunday.getDate() + 6);
        return saturdayDate;
    }

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

    function goToPreviousWeek() {
        if (startDate === null || endDate == null) {
            return;
        }
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
        getTimelineForWeek(prevWeekStart).then((weekly) => {
            // TODO: Get the start and end date
            // Do I make
            setRawTimeline(weekly);
        });
    }

    function goToNextWeek() {
        //
    }

    const formatDate = (date: Date) => {
        return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
        });
    };

    const formatDateMmDdYyyy = (date: Date) => {
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        const year = date.getFullYear();

        return `${month}-${day}-${year}`;
    };

    const parseDateMmDdYyyy = (dateString: string) => {
        // Split date and time
        const [datePart, timePart] = dateString.split(", ");

        // Split date components
        const [month, day, year] = datePart.split("-").map(Number);

        // Split time components
        const [hours, minutes, seconds] = timePart.split(":").map(Number);

        // Create new Date object (month is 0-based, so subtract 1)
        return new Date(year, month - 1, day, hours, minutes, seconds);
    };

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
