// class WeeklyVideoUsageTimeline(BaseModel):
//     days: List[VideoUsageTimeline]

export interface WeeklyVideoTimeline {
    days: VideoUsageTimeline[];
}

// class VideoUsageTimeline(BaseModel):
//     date: datetime
//     videos: List[VideoTimelineContent]
export interface VideoUsageTimeline {
    date: Date;
    videos: VideoTimelineContent[];
}

// class VideoTimelineContent(BaseModel):
//     videoName: str
//     events: List[TimelineEvent]

export interface VideoTimelineContent {
    videoName: string;
    events: VideoTimelineEvent[];
}

// class TimelineEvent(BaseModel):
//     logId: int
//     startTime: datetime
//     endTime: datetime

export interface VideoTimelineEvent {
    logId: number;

    startTime: Date;
    endTime: Date;
}
