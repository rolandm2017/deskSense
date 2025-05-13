import { WatchEntry } from "./historyTracker";

class NetflixFacade {
    constructor() {}

    updateActiveTitle(title: WatchEntry) {
        // TODO: So it goes somewhere that
        // it can be later accessed
        // to give stillHere updates to the server
    }

    sendPlayEventPayload(payload: any) {
        console.log("Sending play event payload:", payload);
    }

    sendPauseEventPayload(payload: any) {
        console.log("Sending pause event payload:", payload);
    }

    injectVideoListeners() {
        console.log("Injecting video listeners");
    }
}

export default NetflixFacade;
