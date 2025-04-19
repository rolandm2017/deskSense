export function getColorFromAppName(appName: string) {
    /* Convert an app name into a color! For coloring charts */
    // Simple hash of string
    let hash = 0;
    for (let i = 0; i < appName.length; i++) {
        hash = appName.charCodeAt(i) + ((hash << 5) - hash);
        hash = hash & hash; // Convert to 32bit integer
    }

    // Get hue from hash (0 to 360)
    const hue = Math.abs(hash) % 360;

    // Fixed saturation and lightness for visual consistency
    const saturation = 65; // %
    const lightness = 50; // %

    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}
