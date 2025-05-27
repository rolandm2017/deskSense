import { DomainInfo, Task } from "./interface/interfaces";
import { YouTubeViewing } from "./videoCommon/visits";

export const taskTypes = {
    REGULAR_DOMAIN: "regular_domain",
    IGNORED_URL: "ignored_url",
    NETFLIX_WATCH_PAGE: "netflix_watch_page",
    YOUTUBE_WATCH_PAGE: "youtube_watch_page",
    YOUTUBE_CHANNEL_PAGE: "youtube_channel_page",
    YOUTUBE_SHORTS: "youtube_shorts",
    YOUTUBE_HOME: "youtube_home",
    ERROR: "task_creation_error",
};

export function isRegularDomainTask(task: Task): task is Task & {
    type: typeof taskTypes.REGULAR_DOMAIN;
    data: { domain: string; tabTitle: string };
} {
    return task.type === taskTypes.REGULAR_DOMAIN;
}

export function isYouTubeWatchPageTask(task: Task): task is Task & {
    type: typeof taskTypes.YOUTUBE_WATCH_PAGE;
    data: YouTubeViewing;
} {
    return task.type === taskTypes.YOUTUBE_WATCH_PAGE;
}

export function isYouTubeShortsTask(task: Task): task is Task & {
    type: typeof taskTypes.YOUTUBE_SHORTS;
    data: DomainInfo;
} {
    return task.type === taskTypes.YOUTUBE_SHORTS;
}

export function isYouTubeHomeTask(task: Task): task is Task & {
    type: typeof taskTypes.YOUTUBE_HOME;
    data: DomainInfo;
} {
    return task.type === taskTypes.YOUTUBE_HOME;
}
