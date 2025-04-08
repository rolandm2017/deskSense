# Might use this later
import time


class FacadeMonitoring:
    def __init__(self, name):
        self.name = name
        self.queue_lengths = []
        self.last_report_time = time.time()
        self.report_interval = 5  # Report every 5 seconds

    def record_queue_length(self, length):
        self.queue_lengths.append(length)

        # Periodically log stats
        current_time = time.time()
        if current_time - self.last_report_time > self.report_interval:
            if self.queue_lengths:
                avg_length = sum(self.queue_lengths) / len(self.queue_lengths)
                max_length = max(self.queue_lengths)
                print(
                    f"{self.name} Queue Stats - Avg: {avg_length:.2f}, Max: {max_length}, Current: {length}")
            self.queue_lengths = []  # Reset
            self.last_report_time = current_time
