import asyncio
import zmq
import zmq.asyncio
from datetime import datetime

import traceback


class MessageReceiver:
    def __init__(self, zmq_url="tcp://127.0.0.1:5555"):
        """Initialize the message receiver with a ZMQ URL."""
        self.zmq_url = zmq_url
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(self.zmq_url)
        # Subscribe to all messages
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

        self.event_queue = asyncio.Queue()
        self.handlers = {}
        self.is_running = False
        self.tasks = []

    def register_handler(self, event_type, handler):
        """
        Register a handler function for a specific event type.

        This is done to hamstring the creeping crawl of async/await
        that would spread through a bunch of code that runs just fine synchronously.
        """
        # If it's already an async function, use it directly
        if asyncio.iscoroutinefunction(handler):
            self.handlers[event_type] = handler
        else:
            # Otherwise, wrap it in an async function
            async def async_wrapper(event):
                handler(event)

            self.handlers[event_type] = async_wrapper

    async def zmq_listener(self):
        """Continuously receive messages from ZMQ and add them to the queue."""
        while self.is_running:
            try:
                message = await self.socket.recv_json()
                await self.event_queue.put(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in ZMQ listener: {e}")

    async def process_events(self):
        """Process events from the queue asynchronously."""
        while self.is_running:
            try:
                event = await self.event_queue.get()
                try:
                    if "type" in event:
                        event_type = event["type"]
                        if event_type in self.handlers:
                            await self.handlers[event_type](event)
                        else:
                            print(
                                f"No handler registered for event type: {event_type}")
                    else:
                        print(
                            f"Unexpected message format (missing 'type'): {event}")

                except Exception as e:
                    print(f"Error processing message: {e}")
                    traceback.print_exc()  # This prints the full traceback
                    raise
                finally:
                    self.event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in event processor: {e}")

    def start(self):
        """Start the message receiver in a way that doesn't require async/await."""
        # Create a new event loop if one doesn't exist
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in current thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self.is_running = True

        # Define the coroutines to run
        async def run_tasks():
            self.tasks = [
                asyncio.create_task(self.zmq_listener()),
                asyncio.create_task(self.process_events())
            ]
            await asyncio.gather(*self.tasks)

        # Run the coroutines in the event loop
        if loop.is_running():
            # If the loop is already running (we're in an async context),
            # create a task
            future = asyncio.ensure_future(run_tasks(), loop=loop)
            return future
        else:
            # If the loop is not running, run it until complete
            try:
                return loop.run_until_complete(run_tasks())
            except KeyboardInterrupt:
                print("Keyboard interrupt received, stopping...")
            finally:
                self.stop()
                loop.close()

    def stop(self):
        """Stop the message receiver."""
        self.is_running = False
        # Cancel any running tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Close ZMQ socket and context
        self.socket.close()
        self.context.term()

    async def async_stop(self):
        """Stop the message receiver asynchronously."""
        self.stop()
        # Give time for tasks to be cancelled
        await asyncio.sleep(0.5)
