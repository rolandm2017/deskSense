# 🧱 Alembic Bridge Migration – April 2025

This project uses Alembic for schema migrations. On April 21, 2025, a special bridge migration (809f06735284) was created to reconcile schema drift between two development environments ("upstairs" and "downstairs" machines).

## What happened?

The "upstairs" dev database was about one month out of date.

Rather than attempting a manual database sync or exporting data, we:

Confirmed the latest applied migration upstairs (37bc06b24c3f)

Compared the upstairs schema to the downstairs (newer) schema

Created a new Alembic migration (809f06735284) that bridges the gap

## What does the bridge do?

This migration:

Drops obsolete tables/columns (e.g., program)

Alters timestamp columns to remove timezone

Adjusts column types (e.g., from text to varchar)

Recreates generated columns where needed

## Should I care?

Nope! Irrelevant now. You can safely treat 809f06735284 as the canonical migration head going forward. From this point on, all development environments should migrate cleanly with:

bash
Copy
Edit
alembic upgrade head
