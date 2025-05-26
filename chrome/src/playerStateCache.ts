import { NetflixViewing, YouTubeViewing } from "./videoCommon/visits";

export class PlayerStateCache {
    /*
        Exists so the extension knows the tab's player state
        and it's available right when the user tabs back into the
        given tab.

        This could mean tabbing in from a different Chrome tab, or
        alt-tabbing back in from a different program.

    */
    cache: Map<number, YouTubeViewing | NetflixViewing>;

    constructor() {
        this.cache = new Map<number, YouTubeViewing | NetflixViewing>();
    }

    contains(tabId: number) {
        return this.cache.has(tabId);
    }

    get(tabId: number) {
        return this.cache.get(tabId);
    }

    set(tabId: number, viewingState: YouTubeViewing | NetflixViewing) {
        this.cache.set(tabId, viewingState);
    }
}

export const playerStateCache = new PlayerStateCache();
