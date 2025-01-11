import { useState } from "react"
import reactLogo from "./assets/react.svg"
import viteLogo from "/vite.svg"
import "./App.css"
import LineChart from "./components/charts/LineChart"
import BarChart from "./components/charts/BarChart"

function App() {
    return (
        <>
            <div>
                <div>
                    <h1>header</h1>
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
    )
}

export default App
