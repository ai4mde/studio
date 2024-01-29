class ChangesChatbot:
    id: str

    def __init__(self, id: str):
        self.id = id

    def prompt(self, message: str) -> str:
        print(f"ID: {self.id}, MSG: {message}", flush=True)
        return "EHLO!"


__all__ = [
    "ChangesChatbot",
]
