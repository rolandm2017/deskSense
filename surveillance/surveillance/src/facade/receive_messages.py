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
                self.stop()  # temporary to silence complaints during tests
                raise

    def start(self):
        """Start the message receiver in a way that doesn't require async/await."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in current thread, so make one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self.is_running = True

        # Define the coroutines to run
        async def run_tasks():
            listener_task = asyncio.create_task(self.zmq_listener(), name="MessageReceiver-zmq_listener")
            processor_task = asyncio.create_task(self.process_events(), name="MessageReceiver-process_events")
            self.tasks = [listener_task, processor_task]
            await asyncio.gather(*self.tasks)

        # Run the coroutines in the event loop
        if loop.is_running():
            # If the loop is already running (we're in an async context),
            # create a task with a specific name
            future = asyncio.create_task(run_tasks(), name="MessageReceiver-main_task")
            # Store this task in our tasks list too
            self.tasks.append(future)
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
        print(f"MessageReceiver: Stopping {len(self.tasks)} tasks")
        self.is_running = False  # First mark as not running to exit loops
        
        # Cancel all tasks and await their cancellation
        tasks_to_cancel = []
        for task in self.tasks:
            if not task.done():
                print(f"MessageReceiver: Cancelling task {task.get_name()}")
                task.cancel()
                tasks_to_cancel.append(task)
        
        if tasks_to_cancel:
            try:
                # Wait for all tasks to complete with a timeout
                # Don't use shield here - it can interfere with proper cancellation
                await asyncio.wait_for(
                    asyncio.gather(*tasks_to_cancel, return_exceptions=True), 
                    timeout=2.0
                )
            except asyncio.TimeoutError:
                print(f"MessageReceiver: {len(tasks_to_cancel)} tasks did not complete in time during shutdown")
            except Exception as e:
                print(f"MessageReceiver: Error awaiting tasks during shutdown: {e}")
        
        # Close ZMQ socket and context if not already closed
        try:
            if hasattr(self, 'socket') and self.socket:
                self.socket.close()
            if hasattr(self, 'context') and self.context:
                self.context.term()
            print("MessageReceiver: ZMQ resources closed")
        except Exception as e:
            print(f"MessageReceiver: Error closing ZMQ resources: {e}")