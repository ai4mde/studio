import json

from channels.generic.websocket import WebsocketConsumer

from ai.services.chatbots.base import BaseChatbot

class ChatConsumer(WebsocketConsumer):
    # No usefull chatbots have yet been implemented
    # If in the future someone wants to do this -> use the base class in ai/services/chatbots/base.py
    chatbots: dict[str, type[BaseChatbot]] = {}
    chatbot: BaseChatbot | None = None

    def connect(self):
        url_arguments = self.scope.get("url_route", {}).get("kwargs")
        selected = url_arguments.get("chatbot")
        self.accept()

        if selected not in self.chatbots:
            self.send(
                text_data=json.dumps(
                    {
                        "message": f"Chatbot {selected} not in available chatbots: {self.chatbots.keys()}",
                    }
                )
            )
            self.close(code=4000)
            return

        self.chatbot = self.chatbots[selected](
            session_id=url_arguments["session"]
        )

        self.send(text_data=json.dumps({"message": "Connected to chatbot"}))

    # this function receives messages on an opened websocket stream and calls chatbot_main to get teh appropriate engine
    # and sends that back through the socket
    def receive(self, text_data=None, bytes_data=None):
        if not self.chatbot:
            return

        if text_data:
            self.send(text_data=json.dumps({"message": self.chatbot.prompt(text_data)}))
