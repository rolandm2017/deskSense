# Design System — DeskSense

## Product Context
- **What this is:** Personal time-tracking dashboard that monitors foreground programs and Chrome tabs, then displays daily/weekly usage data
- **Who it's for:** Single user (the developer), someone who wants honest data about how they spend their time
- **Space/industry:** Personal analytics, time tracking (peers: RescueTime, Toggl, WakaTime, ActivityWatch)
- **Project type:** Data-heavy personal dashboard with charts, timelines, and category breakdowns

## Aesthetic Direction
- **Direction:** Industrial/Utilitarian — like a well-made instrument panel. Serious about data, respectful of attention. Bloomberg Terminal meets a good design studio's internal tools.
- **Decoration level:** Minimal — typography and data density do the work. Hard dividers and rails, not cards with shadows.
- **Mood:** Quiet confidence. Not cold, not cozy. The feeling of a well-organized workspace where everything has a purpose. You open it and feel like you're looking at a serious personal observatory.

## Typography
- **Display/Hero:** Instrument Serif — editorial authority for day headings and big numbers. The serif says "authored, personal" not "SaaS product."
- **Body/UI:** DM Sans — clean, contemporary, good optical sizing range. Handles labels, paragraphs, and navigation.
- **Data/Tables:** IBM Plex Mono — timestamps, durations, domains, percentages. Makes tracking data feel operational and precise. Use `font-variant-numeric: tabular-nums` for aligned columns.
- **Code:** IBM Plex Mono (same as data)
- **Loading:** Google Fonts CDN — `family=DM+Sans:ital,opsz,wght@0,9..40,300..700;1,9..40,300..700&family=IBM+Plex+Mono:wght@400;500;600&family=Instrument+Serif:ital@0;1`
- **Scale:**
  - xs: 10px — fine print, rhythm strip labels
  - sm: 11px — mono labels, uppercase section headers
  - base: 13px — body text, UI labels, category names
  - md: 14px — form inputs, primary body
  - lg: 15px — emphasized body text
  - xl: 28-32px — stat card values (Instrument Serif)
  - 2xl: 42px — page headings like "Monday, April 7" (Instrument Serif)
  - 3xl: 48-56px — hero numbers, landing display (Instrument Serif)

## Color
- **Approach:** Restrained — dark base with category accents. Color is meaningful, never decorative.
- **Background:** `#18191B` — near-black with slight warmth
- **Surface:** `#222528` — cards, panels, right rail
- **Surface-2:** `#2C3033` — inputs, hover states, nested surfaces
- **Text:** `#E8E4DB` — warm off-white, not pure white
- **Text muted:** `#8A8478` — secondary labels, timestamps, percentages
- **Accent:** `#C7F36B` — lime, used sparingly for emphasis and primary actions
- **Accent deep:** `#8DAE32` — darker lime for hover/active states
- **Rule/border:** `#3A3F3E` — subtle dividers, hard rails
- **Category colors:**
  - Productivity: `#C7F36B` (lime)
  - Entertainment: `#F28A2E` (orange)
  - Learning: `#7DD3C7` (teal)
  - Communication: `#E9687A` (coral)
  - Idle: `#6B6560` (warm gray)
- **Semantic:**
  - Success: `#4ADE80` on `#1A2A1A`
  - Warning: `#F28A2E` on `#2A2415`
  - Error: `#E9687A` on `#2A1A1A`
  - Info: `#7DD3C7` on `#1A2A2A`
- **Light mode:** Not planned. Single dark theme.

## Spacing
- **Base unit:** 4px
- **Density:** Comfortable — data-dense inside the active canvas, generous margins at section boundaries
- **Scale:** 2xs(2) xs(4) sm(8) md(12) base(16) lg(24) xl(32) 2xl(48) 3xl(64)

## Layout
- **Approach:** Poster-composition — one dominant chart per viewport, not a grid of interchangeable widgets
- **Grid:** Asymmetric. Main content ~70%, fixed right rail ~280px. Controls at edges, not in toolbars.
- **Max content width:** 1200px
- **Border radius:** Nearly none. sm: 1-2px, md: 4px. No rounded corners on timeline blocks. Square dots for category indicators.
- **Key principles:**
  - One giant chart beats six medium charts
  - Hero chart visible above the fold, always
  - Hard dividers, rails, and bands instead of floating cards
  - Right rail stays fixed while main canvas scrolls
  - Categorization feels like inline annotation, not a settings page

## Motion
- **Approach:** Minimal-functional — only transitions that aid comprehension
- **Easing:** enter(ease-out) exit(ease-in) move(ease-in-out)
- **Duration:** micro(50-100ms) short(150ms) medium(250ms)
- **Rules:**
  - Hover sharpens contrast, never glows
  - No decorative animation
  - Category reassignment causes bars and totals to reflow instantly
  - Page sections reveal in bands, top to bottom

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-07 | Initial design system created | Created by /design-consultation. Industrial/utilitarian direction. Codex and Claude subagent both contributed — agreed on editorial serif typography, asymmetric poster layout, and rejecting standard widget-grid dashboards. Lime accent on dark base chosen to differentiate from Grafana/generic analytics tools. |
| 2026-04-07 | Dark-only, no light mode | Personal tool, single user. Dark reduces eye strain for data-dense screens. Simplifies implementation. |
| 2026-04-07 | Instrument Serif for display | Deliberate risk — most dashboards use sans-serif. The serif gives editorial weight and says "personal" not "SaaS." |
