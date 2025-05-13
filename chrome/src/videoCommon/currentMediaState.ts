import { PlatformType, PlayerState } from "../types/general.types";

class CurrentMediaState {
    currentPlatform: PlatformType;
    videoState: PlayerState;

    constructor(platform: PlatformType) {
        this.currentPlatform = platform;
        this.videoState = "paused"; // default
    }

    setPlaying() {
        this.videoState = "playing";
    }

    setPaused() {
        this.videoState = "paused";
    }
}
