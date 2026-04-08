import { BrowserRouter, Link, Route, Routes } from "react-router-dom";

import Home from "./pages/Home";
import Weekly from "./pages/Weekly";
import { showcaseRoutes } from "./features/charts-showcase";

function App() {
  return (
    <BrowserRouter>
      <div>
        <nav className="border-b border-[var(--ds-rule)] px-8 py-4">
          <div className="mx-auto flex max-w-[1200px] items-center gap-6 font-mono text-[11px] uppercase tracking-[0.08em] text-[var(--ds-text-muted)]">
            <Link className="transition-colors duration-150 hover:text-[var(--ds-text)]" to="/">
              Home
            </Link>
            <Link
              className="transition-colors duration-150 hover:text-[var(--ds-text)]"
              to="/weekly"
            >
              Weekly Reports
            </Link>
            <Link
              className="transition-colors duration-150 hover:text-[var(--ds-text)]"
              to="/showcase/daily"
            >
              Charts Showcase
            </Link>
          </div>
        </nav>

        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/weekly" element={<Weekly />} />
            {showcaseRoutes}
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
