# PostgreSQL Timestamp & Timezone Behavior Documentation

## How PostgreSQL Handles Timezone-Aware Timestamps

PostgreSQL has a specific behavior pattern when dealing with timestamps that include timezone information:

Storage: When a timestamp with timezone (timestamp with time zone, or fields created with DateTime(timezone=True)) is stored, PostgreSQL converts the value to UTC. It does not preserve the original timezone. Only the UTC instant is stored; display-timezone adjustments happen at retrieval.

Retrieval: When querying that timestamp later, PostgreSQL automatically converts it from UTC to the current session's timezone before returning the results.

Session Timezone: Each PostgreSQL connection has a session timezone setting that determines how timezone-aware timestamps are displayed. This can be set using SET TIME ZONE 'timezone'.

## Implications for Application Development

This behavior has several important implications:

Date Shifting: For timestamps near midnight, the date portion may change when viewed in different timezones. For example, a timestamp stored as "2025-03-02 23:00:00 PST" is internally stored as "2025-03-03 07:00:00 UTC", and would appear as "2025-03-03 16:00:00" in Tokyo time.

Hour Distribution: Queries that group by hour will show distributions based on the session's timezone, not necessarily the timezone in which the data was originally recorded or the UTC time.

Consistency: Applications that need to work with consistent timestamps across different timezones should explicitly specify the timezone in queries using AT TIME ZONE 'timezone' or use timezone-naive timestamps.

## How to Control Timezone Conversion

There are several ways to control how PostgreSQL handles timezone conversion:

**View Without Timezone Adjustment**: Cast to timestamp without time zone to strip timezone context, showing the UTC value directly without session-based conversion:

sql `SELECT TO_CHAR(start_time::timestamp, 'HH24:MI:SS');`

**Force UTC Display**: Explicitly convert to UTC:

sql`SELECT TO_CHAR(start_time AT TIME ZONE 'UTC', 'HH24:MI:SS')`

**Specific Timezone**: Convert to any timezone:

sql`SELECT TO_CHAR(start_time AT TIME ZONE 'Asia/Tokyo', 'HH24:MI:SS')`

**zChange Session Timezone**: Change how all timestamp with timezone values are displayed in the current session:

sql`SET TIME ZONE 'America/Los_Angeles';`

Store Local Time: For applications needing both UTC and local time, store two separate columns:
sql`start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True)) # UTC internally`
`start_time_local: Mapped[datetime] = mapped_column(DateTime(timezone=False)) # No conversion`

Understanding these behaviors is crucial for correctly handling date and time data in applications that span multiple timezones.

## Getting at the Truth

To see the data as it's actually stored:

```sql
SELECT TO_CHAR(start_time::timestamp, 'HH24') AS hour, COUNT(\*) AS count
FROM public.program_logs
GROUP BY hour ORDER BY hour;
```

Or to explicitly see the UTC representation:

```sql
SELECT TO_CHAR(start_time AT TIME ZONE 'UTC', 'HH24') AS hour, COUNT(*) AS count
FROM public.program_logs
GROUP BY hour ORDER BY hour;
```

Sources:
https://claude.ai/chat/35966e8b-cf4e-4516-a6d9-0084f29f9ee8
https://chatgpt.com/c/68155d38-cf0c-8010-9fd6-5d35ae15c11c
