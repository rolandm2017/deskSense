// App.tsx
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";

import Home from "./pages/Home";
import Weekly from "./pages/Weekly";

function App() {
    return (
        <BrowserRouter>
            <nav>
                <Link to="/">Home</Link>
                {/* <Link to="/weekly" className="ml-4">
                    Weekly Reports
                </Link> */}
            </nav>

            <Routes>
                <Route path="/" element={<Home />} />
                {/* <Route path="/weekly" element={<Weekly />} /> */}
            </Routes>
        </BrowserRouter>
    );
}

export default App;
