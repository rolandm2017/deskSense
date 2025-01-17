import { useEffect, useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";
import LineChart from "./components/charts/LineChart";
import BarChart from "./components/charts/BarChart";

import {
    getKeyboardReport,
    getMouseReport,
    getProgramReport,
    KeyboardReport,
    MouseReport,
    ProgramActivityReport,
} from "./api/getData.api";

function App() {
    const [keyboardReport, setKeyboardReport] = useState<KeyboardReport|null>(null) // prettier-ignore
    const [mouseReport, setMouseReport] = useState<MouseReport|null>(null) // prettier-ignore
    const [programReport, setProgramReport] = useState<ProgramActivityReport|null>(null); // prettier-ignore

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
                console.log(report.count);
            });
        }
    }, [programReport]);

    return (
        <>
            <div>
                <div>
                    <h1>DeskSense Dashboard</h1>
                </div>
                <div>
                    <h2>Programs</h2>
                    <BarChart />
                </div>
                <div>
                    <h2>Mouse & keyboard</h2>
                    <LineChart />
                </div>
            </div>
        </>
    );
}

export default App;
