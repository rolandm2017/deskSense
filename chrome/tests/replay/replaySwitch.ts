/// <reference types="chrome"/>

import {
    distributeTaskData,
    PlayPauseDispatch,
} from "../../src/backgroundUtil";
import {
    CaptureEvent,
    isAltTabBackInEvent,
    isOnUpdatedCompleteEvent,
    isPlayerStateChangedEvent,
} from "../../src/types/captureEvents.types";
// PLAYER_STATE_CHANGED
// ON_UPDATED_COMPLETE
// PLAYER_STATE_CHANGED

function selectEntryPoint(
    event: CaptureEvent,
    deps: {
        playPauseDispatch: PlayPauseDispatch;
        handleUserTabsBackIn: Function;
        getTaskForDomain: Function;
        distributeTaskData: Function;
    }
) {
    // ALT_TAB_BACK_IN
    if (isAltTabBackInEvent(event)) {
        const activeTab = event.data as chrome.tabs.Tab;
        if (activeTab.url) {
            deps.handleUserTabsBackIn(activeTab.url, activeTab);
        }
        // PLAYER_STATE_CHANGED
    } else if (isPlayerStateChangedEvent(event)) {
        const sender = event.data.sender as chrome.runtime.MessageSender;
        const message = event.data.message;
        if (event.data.message.event === "user_pressed_play") {
            // FIXME: User is able to press pause, somehow, before .setCurrent is called
            // TODO: On close ... i need one PER watch screen. what if user has 5 videos going?
            deps.playPauseDispatch.notePlayEvent(sender);
        } else if (message.event === "user_pressed_pause") {
            deps.playPauseDispatch.notePauseEvent();
        } else if (message.event === "youtube_autoplay") {
            console.log("[autoplay] youtube");
            // IF trySendPlayEvent, BUT no page event report yet,
            // THEN bundle them.
            deps.playPauseDispatch.noteYouTubeAutoPlayEvent(sender);
        } else if (message.event === "netflix_autoplay") {
            console.log("[autoplay] netflix");
            deps.playPauseDispatch.noteNetflixAutoPlayEvent(sender);
        }
        // ON_UPDATED_COMPLETE
    } else if (isOnUpdatedCompleteEvent(event)) {
        console.log("onActivated - getDomainFromUrl");

        const tab = {
            id: event.data.tabId,
            url: event.data.url,
        } as chrome.tabs.Tab;

        // SO this one is, "I switch from Chrome Tab A to Chrome Tab B".
        // The other one is, "I alt tab back IN to Chrome."
        // But the alt-tab-back-into-Chrome one also fires "onActivated".
        // TODO: Find a way to choose between this one and the onMessage focus listener
        const task = deps.getTaskForDomain(tab, (youTubeTask) => {
            distributeTaskData(youTubeTask);
        });
    }
    throw new Error("Failed to accommodate event type: " + event.type);
}
