export function chooseTickValuesSpacing(hours: number, roundedMax: number) {
    // Generate tick values up to the rounded maximum
    if (hours < 3) {
        const fourTicksPerHour = 4;
        const lowUsageTickValues = Array.from(
            { length: Math.floor(roundedMax * fourTicksPerHour) + 1 }, // "4x as many ticks"
            (_, i) => i * 0.25
        );
        return lowUsageTickValues;
    } else if (hours < 6) {
        const twoTicksPerHour = 2;
        const mediumUsageTickValues = Array.from(
            { length: Math.floor(roundedMax * twoTicksPerHour) + 1 }, // "2x as many ticks"
            (_, i) => i * 0.5
        );
        return mediumUsageTickValues;
    } else {
        const highUsageTickValues = Array.from(
            { length: Math.floor(roundedMax) + 1 },
            (_, i) => i
        );
        return highUsageTickValues;
    }
}
