# Gathering dates on Summary models

The following is a description of the rationale for Summary models have a gathering_date field without hh:mm:ss.

## why do i have a gathering date in my DailySummary models?

The gathering date must live in the summary file because otherwise we don't know which date it was gathered on.

## why is the gathering date just the date and not the time?

Sheering off the specific time simplifies the information: The programmer never has to ask whether the specific time really truly is within the desired boundaries chronologically. It's less work to deal with, and further, a SUMMARY of the times recorded throughout the day, cannot at all keep track of when each recording took place. It's beyond the nature of a summation since the mixture is homogenous. You're asking a gallon of water when each cup was added. It doesn't make sense.

Further, by sheering off the specific time, i.e. of the very first entry of the summary's row, you exclude the possibility that the first addition will occur at 6:23 AM, thus necessitating a custom "end_of_day" time being made in the row, to signal to the program, "hey, it's time to move onto the next day's summation." Or worse, that value doesn't exist, and the program merrily continues adding time until 6:23 am the next day. A big problem.

# Gathering dates on Log models

The following is a description of the rationale for Log models have a gathering_date field with hh:mm:ss.

## Explanation of why

Why does the log model have a start_time, end_time, a duration, a gathering date, AND a created_at field?

If you have the created_at time, you know what date it was gathered. Sure, sometimes you might want to be able to BS a value, as in a test. But then I have to look at that created_at field and the gathering_date field, and read the code over and over, ignoring that noise every time. That's a cost.

If you have (a) start_time, and (b) end_time, then you, by definition, have the duration, (c). b - a = c. And, don't tell me it will sometimes be different: that smells. So the DURATION can go. Start and end times must stay, so that I know where in the graph the entry goes. But duration is just a computed column!

### What COULD the gathering date be useful for?

The gathering date could be useful for running queries to select every entry made on x date. I suppose querying "if date == '04-25-2025'" is a bit faster than querying "if date < 'end of day'", and "date > 'start of day'", because then the program only has to check equality and not greater/less than 2x. It's 2x as much work, supposing testing == is as much work as > or <. But it might not be.
