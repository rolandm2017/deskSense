/// <reference types="chrome"/>

import { ServerApi } from "../../src/api";
import { PlayPauseDispatch } from "../../src/backgroundUtil";
import {
    CaptureEvent,
    isOnUpdatedCompleteEvent,
    isPlayerStateChangedEvent,
} from "../../src/types/captureEvents.types";
import { ViewingTracker } from "../../src/videoCommon/visits";
// PLAYER_STATE_CHANGED
// ON_UPDATED_COMPLETE
// PLAYER_STATE_CHANGED

export function replayUsage(
    event: CaptureEvent,
    deps: {
        viewingTracker: ViewingTracker;
        serverApi: ServerApi;
        dispatch: PlayPauseDispatch;
        getTaskForDomain: Function;
        distributeTaskData: Function;
    }
): Promise<void> {
    return new Promise<void>((resolve) => {
        // ALT_TAB_BACK_IN
        if (isPlayerStateChangedEvent(event)) {
            console.log(
                "HERERERE]rkeware",
                console.log(deps.viewingTracker.currentMedia)
            );

            const sender = event.data.sender as chrome.runtime.MessageSender;
            const message = event.data.message;
            if (event.data.message.event === "user_pressed_play") {
                console.log(" in user_pressed_play");
                // FIXME: User is able to press pause, somehow, before .setCurrent is called
                // TODO: On close ... i need one PER watch screen. what if user has 5 videos going?
                deps.dispatch.notePlayEvent(sender);
                resolve();
            } else if (message.event === "user_pressed_pause") {
                console.log(" in user_pressed_pause pause");
                deps.dispatch.notePauseEvent();
                resolve();
            } else if (message.event === "youtube_autoplay") {
                console.log("[autoplay] youtube");
                // IF trySendPlayEvent, BUT no page event report yet,
                // THEN bundle them.
                deps.dispatch.noteYouTubeAutoPlayEvent(sender);
                resolve();
            } else if (message.event === "netflix_autoplay") {
                console.log("[autoplay] netflix");
                deps.dispatch.noteNetflixAutoPlayEvent(sender);
                resolve();
            }
            // ON_UPDATED_COMPLETE
        } else if (isOnUpdatedCompleteEvent(event)) {
            const tab = {
                id: event.data.tabId,
                url: event.data.url,
                // FIXME: Should never happen
                title: event.data.title ?? "Failed to record tab title",
            } as chrome.tabs.Tab;
            console.log(tab, "in on updated complet");

            // SO this one is, "I switch from Chrome Tab A to Chrome Tab B".
            const task = deps.getTaskForDomain(tab, (youTubeTask) => {
                console.log(youTubeTask, "youtube Task");
                // FIXME: Need to accommodate the callback problem
                deps.distributeTaskData(
                    youTubeTask,
                    deps.serverApi,
                    deps.viewingTracker
                );
                resolve();
            });
            if (task) {
                console.log("Task: ", task);
                deps.distributeTaskData(
                    task,
                    deps.serverApi,
                    deps.viewingTracker
                );
                resolve();
            }
        } else {
            console.log("Fail:", event);
            throw new Error("Failed to accommodate event type: " + event.type);
        }
    });
}
