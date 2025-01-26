from pathlib import Path


class VideoPathManager:
    def __init__(self, project_root="."):
        self.output_dir = Path(project_root) / 'output'
        self.raw = self.output_dir / 'raw_recordings'
        self.processed = self.output_dir / 'processed'
        self.discard = self.output_dir / 'discard'

        # Create directories if they don't exist
        for dir in [self.raw, self.processed, self.discard]:
            dir.mkdir(parents=True, exist_ok=True)

    def raw_path(self, filename):
        return self.raw / filename

    def processed_path(self, filename):
        return self.processed / filename

    def discard_path(self, filename):
        return self.discard / filename


# # Usage
# paths = VideoPathManager('/path/to/project')

# # Writing files
# with open(paths.raw_path('video1.mp4'), 'wb') as f:
#     f.write(raw_video_data)

# with open(paths.processed_path('video1.mp4'), 'wb') as f:
#     f.write(processed_video_data)
