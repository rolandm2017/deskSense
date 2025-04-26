# Import the original class
from surveillance.src.facade.receive_messages import MessageReceiver

class MockMessageReceiver(MessageReceiver):
    def __init__(self, zmq_url="tcp://127.0.0.1:5555"):
        """Initialize the mock without actually setting up ZMQ connections"""
        # Don't call super().__init__() to avoid actual ZMQ setup
        self.zmq_url = zmq_url
        self.handlers = {}
        self.is_running = False
        self.start_called = False
        self.stop_called = False
        # Add dummy attributes expected by inherited methods
        self.context = None
        self.socket = None
        self.tasks = []
        self.event_queue = None

    # Override the critical methods
    def start(self):
        """Mock the start method."""
        self.is_running = True
        self.start_called = True
        print("[MockMessageReceiver] Started")
        return None

    def stop(self):
        """Mock the stop method."""
        self.is_running = False
        self.stop_called = True
        print("[MockMessageReceiver] Stopped")
        
    async def async_stop(self):
        """Mock the async_stop method."""
        self.stop()
        
    # Keep the register_handler method from the original class
    # So we don't have to reimplement it
    
    # Add our test helper
    def simulate_message(self, message):
        """Simulate receiving a message and process it with the appropriate handler."""
        if not self.is_running:
            print("[MockMessageReceiver] Cannot simulate message - not running")
            return False
            
        if "type" not in message:
            print("[MockMessageReceiver] Message missing 'type' field")
            return False
            
        event_type = message["type"]
        if event_type not in self.handlers:
            print(f"[MockMessageReceiver] No handler for event type: {event_type}")
            return False
            
        handler = self.handlers[event_type]
        print(f"[MockMessageReceiver] Processing simulated {event_type} message")
        
        import asyncio
        if asyncio.iscoroutinefunction(handler):
            asyncio.create_task(handler(message))
        else:
            handler(message)
        
        return True