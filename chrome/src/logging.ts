import chalk from "chalk";

console.log();
console.log(chalk.magenta("[Netflix]"), "⏸️ pause");

type PlatformType = "YouTube" | "Netflix";

class PlatformLogger {
    platform: PlatformType;
    insert: string;
    constructor(platform: PlatformType) {
        this.platform = platform;

        if (platform === "YouTube") {
            this.insert = "[YouTube]";
        } else {
            this.insert = "[Netflix]";
        }
    }

    logPlayEvent() {
        console.log(chalk.red(this.insert), "▶️ play");
    }

    logPauseEvent() {
        console.log(chalk.red(this.insert), "⏸️ pause");
    }
}

class DomainLogger {
    constructor() {}

    logTabSwitch() {
        console.log("🌐 [API] 🌍  Switched to domain: youtube.com");
    }
}
