import signal
import sys
from typing import Callable, Optional

class InterruptHandler:
    def __init__(self, cleanup_callback: Optional[Callable] = None):
        """
        Initialize the interrupt handler.
        
        Args:
            cleanup_callback: Optional callback function to be executed during cleanup
        """
        self.cleanup_callback = cleanup_callback
        self._setup_signal_handling()
    
    def _setup_signal_handling(self):
        """Set up the SIGINT signal handler."""
        
        signal.signal(signal.SIGINT, self._handle_interrupt)
    
    def _handle_interrupt(self, signum: int, frame) -> None:
        """
        Handle the interrupt signal.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        print("\nReceived interrupt signal. Cleaning up...")
        
        if self.cleanup_callback:
            self.cleanup_callback()
            
        # Re-raise the signal after cleanup
        
        signal.default_int_handler(signum, frame)
    
    def register_cleanup_callback(self, callback: Callable) -> None:
        """
        Register a cleanup callback to be executed when interrupt occurs.
        
        Args:
            callback: Function to be called during cleanup
        """
        
        self.cleanup_callback = callback