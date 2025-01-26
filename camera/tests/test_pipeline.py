#
# Record ten minutes of video, one vid per min.
# See that, after the test, transformations worked.
# See the black where there's stillness.
# Stillness, it's put into separate video.
# samples/raw_recordings
# samples/processed
# samples/discard  <--- here goes the still sections
#
#
import os
import cv2
import numpy as np
from datetime import datetime
import json
from pathlib import Path


class VideoTestFramework:
    def __init__(self, base_dir="test_out"):
        self.base_dir = Path(base_dir)
        self.processed_dir = self.base_dir / "processed"
        self.discard_dir = self.base_dir / "discard"
        self.results_dir = self.base_dir / "results"
        self.setup_directories()

    def setup_directories(self):
        """Create necessary directories if they don't exist."""
        for dir_path in [self.processed_dir, self.discard_dir, self.results_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def verify_black_frames(self, video_path, threshold=5):
        """
        Verify that frames marked as still are truly black.
        Returns percentage of correctly processed frames and list of problematic timestamps.
        """
        cap = cv2.VideoCapture(str(video_path))
        issues = []
        total_frames = 0
        incorrect_frames = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Check if frame should be black (assuming motion detection already processed)
            frame_mean = np.mean(frame)
            if frame_mean > threshold:  # Non-black frame detected
                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / \
                    1000.0  # Convert to seconds
                issues.append({
                    'timestamp': timestamp,
                    'frame_mean': float(frame_mean)
                })
                incorrect_frames += 1
            total_frames += 1

        cap.release()
        accuracy = (total_frames - incorrect_frames) / total_frames * 100
        return accuracy, issues

    def verify_stillness(self, video_path, motion_threshold=0.5):
        """
        Verify that discarded clips are truly still.
        Returns percentage of truly still frames and list of frames with motion.
        """
        cap = cv2.VideoCapture(str(video_path))
        issues = []
        total_frames = 0
        motion_frames = 0
        prev_frame = None

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if prev_frame is not None:
                # Calculate frame difference
                diff = cv2.absdiff(prev_frame, frame)
                motion = np.mean(diff)

                if motion > motion_threshold:
                    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                    issues.append({
                        'timestamp': timestamp,
                        'motion_value': float(motion)
                    })
                    motion_frames += 1

            prev_frame = frame
            total_frames += 1

        cap.release()
        accuracy = (total_frames - motion_frames) / total_frames * 100
        return accuracy, issues

    def run_batch_test(self):
        """
        Run tests on all videos in processed and discard directories.
        Generate comprehensive report.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            'timestamp': timestamp,
            'processed_videos': [],
            'discarded_videos': [],
            'overall_accuracy': 0.0
        }

        # Test processed videos (black frame verification)
        for video_file in self.processed_dir.glob('*.mp4'):
            accuracy, issues = self.verify_black_frames(video_file)
            results['processed_videos'].append({
                'filename': video_file.name,
                'accuracy': accuracy,
                'issues': issues
            })

        # Test discarded videos (stillness verification)
        for video_file in self.discard_dir.glob('*.mp4'):
            accuracy, issues = self.verify_stillness(video_file)
            results['discarded_videos'].append({
                'filename': video_file.name,
                'accuracy': accuracy,
                'issues': issues
            })

        # Calculate overall accuracy
        all_accuracies = [v['accuracy'] for v in results['processed_videos']]
        all_accuracies.extend([v['accuracy']
                              for v in results['discarded_videos']])
        results['overall_accuracy'] = sum(
            all_accuracies) / len(all_accuracies) if all_accuracies else 0

        # Save results
        results_file = self.results_dir / f"test_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=4)

        return results

    def generate_report(self, results):
        """Generate a human-readable report from test results."""
        report = f"""Video Processing Test Report
            Generated: {results['timestamp']}

            Overall Accuracy: {results['overall_accuracy']:.2f}%

            Processed Videos Analysis:
            ------------------------"""

        for video in results['processed_videos']:
            report += f"\n\nFilename: {video['filename']}"
            report += f"\nAccuracy: {video['accuracy']:.2f}%"
            if video['issues']:
                report += f"\nIssues Found: {len(video['issues'])}"
                report += "\nFirst 5 issues:"
                for issue in video['issues'][:5]:
                    report += f"\n  - At {issue['timestamp']:.2f}s: Mean pixel value = {issue['frame_mean']:.2f}"

        report += "\n\nDiscarded Videos Analysis:"
        report += "\n------------------------"

        for video in results['discarded_videos']:
            report += f"\n\nFilename: {video['filename']}"
            report += f"\nAccuracy: {video['accuracy']:.2f}%"
            if video['issues']:
                report += f"\nIssues Found: {len(video['issues'])}"
                report += "\nFirst 5 issues:"
                for issue in video['issues'][:5]:
                    report += f"\n  - At {issue['timestamp']:.2f}s: Motion value = {issue['motion_value']:.2f}"

        return report


# Example usage
if __name__ == "__main__":
    test_framework = VideoTestFramework()
    results = test_framework.run_batch_test()
    report = test_framework.generate_report(results)

    # Save report
    report_path = test_framework.results_dir / \
        f"report_{results['timestamp']}.txt"
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"Testing completed. Overall accuracy: {
          results['overall_accuracy']:.2f}%")
    print(f"Detailed report saved to: {report_path}")
