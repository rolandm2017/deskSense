import { useEffect, useState } from "react";
import "../App.css";

import {
    getWeeklyChromeUsage,
    getWeeklyProgramUsage,
} from "../api/getData.api";
import {
    WeeklyChromeUsage,
    WeeklyProgramUsage,
} from "../interface/api.interface";

function Weekly() {
    const [weeklyChrome, setWeeklyChrome] = useState<WeeklyChromeUsage | null>(
        null
    );
    const [weeklyPrograms, setWeeklyPrograms] =
        useState<WeeklyProgramUsage | null>(null);

    useEffect(() => {
        getWeeklyChromeUsage().then((weekly) => {
            setWeeklyChrome(weekly);
        });
        getWeeklyProgramUsage().then((weekly) => {
            setWeeklyPrograms(weekly);
        });
    }, []);

    useEffect(() => {
        if (!weeklyChrome && !weeklyPrograms) {
            return;
        }
        console.log(weeklyChrome);
        console.log(weeklyPrograms);
    }, [weeklyChrome, weeklyPrograms]);

    return (
        <>
            <div>
                <h2>Weekly Reports</h2>
                <div>
                    <h3>Current Week</h3>
                    {/* // TODO: Show the DATES being displayed, the range. */}
                    {/* // "Showing Sunday 22 to ..." */}
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
