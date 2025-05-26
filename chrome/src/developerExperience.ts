export function helpDeveloperNoticeMissingNpmRunBuild() {
    const lastBuiltTimestampString = process.env.BUILD_TIMESTAMP as string;

    if (lastBuiltTimestampString === undefined) {
        throw new Error("Failed to get the Build Timestamp");
    }

    const lastBuiltTimestamp = new Date(lastBuiltTimestampString);
    const now = new Date();

    // Cast to number to satisfy TypeScript
    const hoursSinceBuild = Math.round(
        (now.getTime() - lastBuiltTimestamp.getTime()) / (1000 * 60 * 60)
    );
    console.log(now.getTime() - lastBuiltTimestamp.getTime());
    const minutesSinceBuild = Math.round(
        (now.getTime() - lastBuiltTimestamp.getTime()) / (1000 * 60)
    );

    const secondsSinceBuild = Math.round(
        (now.getTime() - lastBuiltTimestamp.getTime()) / 1000
    );

    if (hoursSinceBuild === 0) {
        console.log(
            `Loading build from ${minutesSinceBuild} minutes and ${secondsSinceBuild} seconds ago`
        );
    } else {
        console.log(`Loading build from ${hoursSinceBuild} hours ago`);
    }
}
