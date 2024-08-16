from ninja import Router

from prose.api.schemas.audio import TextSchema, SpeechSchema

audio = Router()

@audio.get('/stt', response=TextSchema)
def speech_to_text(request, input_audio: SpeechSchema):
    # TODO: implementation goes here

    return None # TODO: return type must match SpeechSchema


@audio.get('/tts', response=SpeechSchema) 
def text_to_speech(request, input_text: TextSchema):
    # TODO: implementation goes here

    return None # TODO: return type must match TextSchema

__all__ = ["audio"]
