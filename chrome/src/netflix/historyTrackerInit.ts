import { WatchHistoryTracker } from "./historyTracker";
import { storageApi } from "./storageApi";

// Initialize the tracker when popup loads
// Made this file to avoid accidentally running this in a test
export const historyTracker = new WatchHistoryTracker(storageApi);
