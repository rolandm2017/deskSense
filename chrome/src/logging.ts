import chalk from "chalk";

import { PlatformType } from "./types/general.types";

console.log();
console.log(chalk.magenta("[Netflix]"), "⏸️  pause");

export class PlatformLogger {
    platform: PlatformType;
    insert: string;
    chalkColor: Function;

    constructor(platform: PlatformType) {
        this.platform = platform;

        if (platform === "YouTube") {
            this.chalkColor = chalk.red;
            this.insert = "[YouTube]";
        } else {
            this.chalkColor = chalk.magenta;
            this.insert = "[Netflix]";
        }
    }

    logLandOnPage(tabTitle: string) {
        // TODO: Make Netflix magenta
        console.log(
            this.chalkColor(this.insert),
            "[info] On page: " + tabTitle
        );
    }

    logPlayEvent(mediaTitle?: string) {
        console.log(
            this.chalkColor(this.insert),
            "▶️  play " + mediaTitle ? ":: " + mediaTitle : ""
        );
    }

    logPauseEvent(mediaTitle?: string) {
        console.log(
            this.chalkColor(this.insert),
            "⏸️  pause " + mediaTitle ? ":: " + mediaTitle : ""
        );
    }
}

class DomainLogger {
    constructor() {}

    logTabSwitch() {
        console.log("🌐 [API] 🌍  Switched to domain: youtube.com");
    }
}
