import { initializedServerApi } from "../api";
import { InputCaptureManager } from "./inputCaptureManager";
import { systemInputCapture } from "./systemInputLogger";

export const captureManager = new InputCaptureManager(
    systemInputCapture,
    initializedServerApi
);
