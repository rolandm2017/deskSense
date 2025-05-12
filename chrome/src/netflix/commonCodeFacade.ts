class NetflixFacade {
    constructor() {}

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
