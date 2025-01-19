import { useEffect, useState } from "react";
import "./App.css";
import LineChart from "./components/charts/LineChart";
import BarChart from "./components/charts/BarChart";

import {
    getKeyboardReport,
    getMouseReport,
    getProgramReport,
} from "./api/getData.api";
import { BarChartColumn } from "./interface/misc.interface";
import {
    KeyboardReport,
    MouseReport,
    ProgramActivityLog,
    ProgramActivityReport,
} from "./interface/api.interface";
import TimelineWrapper from "./components/charts/Timeline";

function App() {
    const [keyboardReport, setKeyboardReport] = useState<KeyboardReport|null>(null) // prettier-ignore
    const [mouseReport, setMouseReport] = useState<MouseReport|null>(null) // prettier-ignore
    const [programReport, setProgramReport] = useState<ProgramActivityReport|null>(null); // prettier-ignore

    const [barsInput, setBarsInput] = useState<BarChartColumn[]>([]);

    const hours = 36000000; // 1000 * 60 * 60

    function processTimeReports(
        reports: ProgramActivityLog[]
    ): BarChartColumn[] {
        // Create a hashtable to store total time per window
        const windowTimes: { [key: string]: number } = {};

        // Calculate time differences and aggregate
        reports.forEach((report: ProgramActivityLog) => {
            const startTime = new Date(report.startTime);
            const endTime = new Date(report.endTime);
            const durationInHours =
                (endTime.getTime() - startTime.getTime()) / hours; // Convert to hours

            if (windowTimes[report.window]) {
                windowTimes[report.window] += durationInHours;
            } else {
                windowTimes[report.window] = durationInHours;
            }
        });

        // Convert to BarChartColumn array and sort by hours spent
        const chartData: BarChartColumn[] = Object.entries(windowTimes)
            .map(([programName, hoursSpent]) => ({
                programName,
                hoursSpent: Number(hoursSpent.toFixed(4)), // Round to 4 decimal places
            }))
            .sort((a, b) => b.hoursSpent - a.hoursSpent);

        return chartData;
    }

    useEffect(() => {
        // TEMP
        console.log(barsInput.length, programReport, "61ru");
        if (barsInput.length == 0 && programReport) {
            console.log(programReport, "63ru");
            const tally = processTimeReports(programReport.programLogs);
            console.log(tally, "65ru");
            setBarsInput(tally);
            // const barsCols: BarChartColumn[] = [
            //     {
            //         programName: "Foo",
            //         hoursSpent: 5.5,
            //     },
            //     {
            //         programName: "Bar",
            //         hoursSpent: 3.1,
            //     },
            //     {
            //         programName: "Baz",
            //         hoursSpent: 4.8,
            //     },
            //     {
            //         programName: "Quux",
            //         hoursSpent: 1.2,
            //     },
            // ];
            // setBarsInput(barsCols);
        }
    }, [barsInput, programReport]);

    useEffect(() => {
        if (keyboardReport === null) {
            getKeyboardReport().then((report) => {
                setKeyboardReport(report);
                console.log(report.count);
            });
        }
    }, [keyboardReport]);

    useEffect(() => {
        if (mouseReport === null) {
            getMouseReport().then((report) => {
                setMouseReport(report);
                console.log(report.count);
            });
        }
    }, [mouseReport]);

    useEffect(() => {
        if (programReport === null) {
            getProgramReport().then((report) => {
                setProgramReport(report);
                console.log(report, "111ru");
            });
        }
    }, [programReport]);

    return (
        <>
            <div>
                <div>
                    <h1>DeskSense Dashboard</h1>
                </div>
                <div style={{ border: "5px solid black" }}>
                    <h2>Programs {programReport?.count.toString()}</h2>
                    <BarChart barsInput={barsInput} />
                </div>
                <div>
                    <h2>
                        Keyboard & Mouse: {keyboardReport?.count},{" "}
                        {mouseReport?.count}
                    </h2>
                    <TimelineWrapper />
                </div>
            </div>
        </>
    );
}

export default App;
