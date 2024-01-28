from django.urls import path
from prompt.consumers.chatbot import ChatConsumer

urls = [
    path('chat/<str:chatbot>/<str:session>', ChatConsumer.as_asgi())
]
