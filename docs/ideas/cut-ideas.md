---
status: log
---

# Cut ideas

Features considered and deliberately deferred or dropped. Each entry records
what was cut and why, so future work can revisit with full context.

## Hover-to-top-3 tooltip on hour chips

Cut from the Commitment Gap page (`spec/commitment-gap-*.md`, seeded from
`docs/ideas/2026-04-13-commitment-gap.md`). The original proposal put a
tooltip on each hour chip listing the top three activities inside that hour,
so the user could skim the day without clicking. It was cut because the chip
itself — and later, the minute-resolution color blocks that replaced chips —
should communicate the hour's shape at a glance; the deeper truth belongs
behind a click to receipts, not a hover. Example: hovering the 2–3pm chip
would have shown `YouTube 22m · VS Code 14m · Chrome 9m`; instead, the block
colors now convey that directly and clicking opens the raw activities.
