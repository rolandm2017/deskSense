from datetime import datetime, timedelta
import random


class MockMouseMove:
    def __init__(self, id, start_time, end_time):
        self.id = id
        self.start_time = start_time
        self.end_time = end_time

    def __repr__(self):
        return f"MouseMove(id={self.id}, start_time={self.start_time})"


class MockMouseDao:
    def __init__(self, *args, **kwargs):
        # Ignore any arguments to match the real DAO's signature
        self._generate_fake_data()

    def _generate_fake_data(self, seed=42):
        """Generate a set of fake mouse movements over the past 24 hours"""
        random.seed(seed)
        self.fake_data = []
        base_time = datetime.now() - timedelta(days=1)

        # Generate 50 random mouse movements
        for i in range(50):
            # Random start time within last 24 hours
            start_offset = timedelta(
                hours=random.uniform(0, 24),
                minutes=random.uniform(0, 60)
            )
            start_time = base_time + start_offset

            # Movement duration between 0.5 and 10 seconds
            duration = timedelta(seconds=random.uniform(0.5, 10))
            end_time = start_time + duration

            self.fake_data.append(
                MockMouseMove(i + 1, start_time, end_time)
            )

        # Sort by end_time to match real database behavior
        self.fake_data.sort(key=lambda x: x.end_time)
        random.seed()

    async def create(self, start_time: datetime, end_time: datetime):
        """Simulate creating a new mouse movement"""
        new_id = len(self.fake_data) + 1
        new_move = MockMouseMove(new_id, start_time, end_time)
        self.fake_data.append(new_move)
        return new_move

    async def read(self, mouse_move_id: int | None = None):
        """Simulate reading from database"""
        if mouse_move_id:
            for move in self.fake_data:
                if move.id == mouse_move_id:
                    return move
            return None
        return self.fake_data

    async def read_past_24h_events(self):
        """Simulate reading past 24h events"""
        cutoff_time = datetime.now() - timedelta(days=1)
        return [
            move for move in self.fake_data
            if move.end_time >= cutoff_time
        ]

    async def delete(self, mouse_move_id: int):
        """Simulate deleting a mouse movement"""
        for i, move in enumerate(self.fake_data):
            if move.id == mouse_move_id:
                return self.fake_data.pop(i)
        return None

    async def process_queue(self):
        """Mock the queue processing - does nothing in the mock"""
        pass

    async def _save_batch(self, batch):
        """Mock batch saving - does nothing in the mock"""
        pass
