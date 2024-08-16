from ninja import Schema

# TODO: you might want to add extra data to these schemas (e.g. timestamps, headers, ...) if needed

class TextSchema(Schema):
    text: str

class SpeechSchema(Schema):
    audio: str # TODO: change to desired type
    
__all__ = [
    "TextSchema",
    "SpeechSchema"
]
