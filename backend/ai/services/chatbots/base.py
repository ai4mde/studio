from abc import ABC, abstractmethod


class BaseChatbot(ABC):
    def __init__(self, session_id: str):
        self.session_id = session_id

    @abstractmethod
    def prompt(self, message: str) -> str:
        """Process a user message and return a response."""
        pass
