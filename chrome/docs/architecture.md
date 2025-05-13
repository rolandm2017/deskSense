# Architecture

The Chrome extension tracks tab changes. "What domain did the user just change to?"

A simple tab change notification sent to the server covers this.

The ext also covers YouTube and Netflix time tracking.

## Mechanisms

YouTube and Netflix use different mechanisms.

Both use a video player listener. Location: chrome/src/videoCommon/videoListeners.ts

The video has a play/pause event listener attached. The listener updates the extension.

### Commonalities

Play/pause events go from the video element, through the code to an endpoint.

The endpoint notifies the server that the user started/stopped the video.

### Differences

##### YouTube

On YouTube, they present the channel name and video title plainly. All you need to do is wait for React to finish rendering the content and it's there.
So something called the ChannelExtractor runs, looks at the DOM, gets the channel name out of the element located right below the video.
The video title comes plainly from the tab's title. It's "just there."

##### Netflix

Netflix makes every effort to obscure information from all kinds of scraping and programmatic access.

Trying to extract the info programmatically is a losing battle. Hence the user is asked via modal what the content title is.
