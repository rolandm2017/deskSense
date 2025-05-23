// Auto-generated from Pydantic models

export interface YouTubeTabChange {
  videoId: string;
  tabTitle: string;
  channel: string;
  url: string;
  startTime: string;
  playerState: any;
}

export interface YouTubePlayerChange {
  videoId: string;
  url: string;
  tabTitle: string;
  channel: string;
  eventTime: string;
  playerState: any;
}

export interface NetflixTabChange {
  tabTitle: string;
  url: string;
  startTime: string;
  videoId: string;
  playerState: any;
}

export interface NetflixPlayerChange {
  tabTitle: string;
  url: string;
  eventTime: string;
  videoId: string;
  showName: string;
  playerState: any;
}

