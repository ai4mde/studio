from django.urls import path
from prompt.consumers.chatbot import ChatConsumer

urls = [
    path('/chat/<chatbot:slug>/<session:slug>', ChatConsumer.as_asgi())
]
