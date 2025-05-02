from abc import ABC, abstractmethod
from typing import Dict, Generator


class ProgramFacadeInterface(ABC):
    """
    Interface class that defines the contract for program facades.
    This class should be inherited by both UbuntuProgramFacade and WindowsProgramFacade.
    """
    
    @abstractmethod
    def listen_for_window_changes(self) -> Generator[Dict, None, None]:
        """
        Listens for window focus changes and yields window information when changes occur.
        
        Yields:
            Dict: Information about the new active window after each focus change.
        """
        pass

    @abstractmethod
    def setup_window_hook(self) -> Generator[Dict, None, None]:
        """
        Sets up a hook to detect window focus changes.
        
        Returns:
            Generator[Dict, None, None]: A generator that yields information about
            the active window when focus changes.
        """
        pass
    
