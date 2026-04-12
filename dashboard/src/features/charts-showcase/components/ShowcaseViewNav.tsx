import { NavLink } from "react-router-dom";

function ShowcaseViewNav() {
  const baseClassName =
    "relative px-6 py-3 font-mono text-[11px] font-medium uppercase tracking-[0.08em] transition-colors duration-150";

  return (
    <nav className="mb-12 flex border-b border-[var(--ds-rule)]">
      <NavLink
        to="/showcase/daily"
        className={({ isActive }) =>
          `${baseClassName} ${
            isActive ? "text-[var(--ds-accent)] after:absolute after:bottom-[-1px] after:left-0 after:right-0 after:h-px after:bg-[var(--ds-accent)]" : "text-[var(--ds-text-muted)] hover:text-[var(--ds-text)]"
          }`
        }
      >
        Today
      </NavLink>
      <NavLink
        to="/showcase/weekly"
        className={({ isActive }) =>
          `${baseClassName} ${
            isActive ? "text-[var(--ds-accent)] after:absolute after:bottom-[-1px] after:left-0 after:right-0 after:h-px after:bg-[var(--ds-accent)]" : "text-[var(--ds-text-muted)] hover:text-[var(--ds-text)]"
          }`
        }
      >
        This Week
      </NavLink>
      <NavLink
        to="/showcase/pursuits-setup"
        className={({ isActive }) =>
          `${baseClassName} ${
            isActive ? "text-[var(--ds-accent)] after:absolute after:bottom-[-1px] after:left-0 after:right-0 after:h-px after:bg-[var(--ds-accent)]" : "text-[var(--ds-text-muted)] hover:text-[var(--ds-text)]"
          }`
        }
      >
        Pursuit Setup
      </NavLink>
    </nav>
  );
}

export default ShowcaseViewNav;
