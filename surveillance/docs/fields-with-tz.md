# tz or not?

Much clarity can be gained on this subject by asking yourself:

How does the program deal with the user changing timezones?

The user lives in Toronto. They spend 19 months in a row with everything being recorded in EST. Then, they take a two week long vacation to Dubai.

How does the program load the user's dashboard when they're in Dubai, properly, if the EST tz isn't attached?

How does the program record data from the Dubai vacation and then show it properly upon return to EST?

## The upside of naive datetime

A naive datetime makes every write simple: The local timezone (LTZ) is converted to UTC and stored. To get the info back, a read occurs, UTC is converted to LTZ, and it's sent to the user's client. It's convenient and handles a lot of the potential jobs really well.

## The moving user problem

But how, then, does the program know which LTZ to return the data to? If the user had a fixed LTZ his whole life, it would be no problem. But, people vacation. They move.

Storing tz-agnostic data can't work for this program. There is a permanent loss of detail if the LTZ is omitted from db cols concerned with time.

## Conclusion

Hence every model that has a start_time and end_time must include a timezone for the field.

The program must function even when the user changes timezones six times in a year.
