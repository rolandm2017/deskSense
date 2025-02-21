// App.tsx
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";

import Home from "./pages/Home";
import Weekly from "./pages/Weekly";

function App() {
    return (
        <BrowserRouter>
            <div className="">
                {" "}
                {/* Add consistent padding container */}
                <nav className="mb-4 mt-4">
                    {" "}
                    {/* Add bottom margin to nav */}
                    <Link to="/">Home</Link>
                    <Link to="/weekly" className="ml-4">
                        Weekly Reports
                    </Link>
                </nav>
                <main>
                    {" "}
                    {/* Wrap routes in main element */}
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/weekly" element={<Weekly />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    );
}

export default App;
