# Session polling

The KeepAliveEngine adds ten sec to the activity's duration, every completed ten sec.

If the activity ends before ten sec is up, the used portion will be added.

It used to be that the KeepAliveEngine would add ten sec at the beginning of a 10 sec window, and deduct the unused portion when the session was swapped out. That was problematic psychologically. It's a lot more work to think about, with many more twists and turns, to imagine, +10, +10, +10, and then on the final loop, "Oh, +10, but only 7 was used, so we have to deduct 3, and did I get the sign right? Did I start with the right value?"

So it was changed to be, "ten sec is added at the end of the 10 sec window. If only (10 - t) seconds are used, (10 - t) seconds will be added in .conclude()"

It's simpler to think about, to understand, simpler to test, and thus less prone to bugs.
