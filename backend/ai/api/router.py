from django.urls import path

from ai.consumers.chatbot import ChatConsumer


websocket_routes = [
    path("chat/<str:chatbot>/<str:session>", ChatConsumer.as_asgi()),
]