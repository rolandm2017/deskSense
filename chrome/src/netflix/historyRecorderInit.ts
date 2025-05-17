import { HistoryRecorder, MessageRelay } from "./historyRecorder";
import { storageApi } from "./storageApi";

// Initialize the tracker when popup loads
// Made this file to avoid accidentally running this in a test.
//
// BTW you can only access this thing in the Netflix content script.
export const historyRecorder = new HistoryRecorder(
    storageApi,
    new MessageRelay()
);
