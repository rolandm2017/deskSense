# tz or not?

Much clarity can be gained on this subject by asking yourself:

How does the program deal with the user changing timezones?

The user lives in Toronto. They spend 19 months in a row with everything being recorded in EST. Then, they take a two week long vacation to Dubai.

How does the program load the user's dashboard when they're in Dubai, properly, if the EST tz isn't attached?

How does the program record data from the Dubai vacation and then show it properly upon return to EST?

Hence the program must retain knowledge of the timezone when querying the db. The user goes on vacation, wants to check their hours. The program sees that the writes were made in EST, so they're displayed in EST, even if the client machine is now in Asia/Tokyo.

## The upside of naive datetime

A naive datetime makes every write simple: The local timezone (LTZ) is converted to UTC and stored. To get the info back, a read occurs, UTC is converted to LTZ, and it's sent to the user's client. It's convenient and handles a lot of the potential jobs really well.

## The moving user problem

But how, then, does the program know which LTZ to return the data to? If the user had a fixed LTZ his whole life, it would be no problem. But, people vacation. They move.

Storing tz-agnostic data can't work for this program. There is a permanent loss of detail if the LTZ is omitted from db cols concerned with time.

## Conclusion

Hence every model that has a start_time and end_time must include a timezone for the field.

The program must function even when the user changes timezones six times in a year.

# April 30: Storing the local timezone

So, pg converts from LTZ to UTC before storing. 12:00 Asia/Tokyo, +9 UTC, is stored at 3:00 UTC.

When PG reads these values back out, it doesn't convert back automatically. They're still in UTC. It's a lot of work to have PG add them back on.
"""
Estimated time:
⏱️ ~5–10 milliseconds total for 2,000 rows (often lower if cached).

PostgreSQL AT TIME ZONE ~5–10 ms for 2k rows × 3 cols.
"""

-   ChatGPT and Claude

So the models will now store both a tz-aware and a tz-naive version of start_time, end_time, gathering_date. These fields will have a \_local ending.

The goal is to make it fast and efficient to query the data, which is in UTC for many fields, and then after it's read, use the \_local fields in the code.

These fields will have to have the tzinfo attached to the object after being read.

This also means storing more harddrive space:

"""
start_time_local (timestamp without timezone): 5,000 rows × 8 bytes = 40,000 bytes
end_time_local (timestamp without timezone): 5,000 rows × 8 bytes = 40,000 bytes
gathering_date_local (timestamp without timezone): 5,000 rows × 8 bytes = 40,000 bytes

Total bytes: 40,000 + 40,000 + 40,000 = 120,000 bytes
Converting to megabytes: 120,000 bytes / 1,024 / 1,024 = 0.114 MB (approximately 0.11 MB)
"""

Convert to 365 days in a year, and you get 41.77 MB.
