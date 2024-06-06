import json

from channels.generic.websocket import WebsocketConsumer

from prompt.chatbots import ChangesChatbot


class ChatConsumer(WebsocketConsumer):
    chatbots = {
        "changes": ChangesChatbot,
    }
    chatbot = None

    def connect(self):
        url_arguments = self.scope.get("url_route", {}).get("kwargs")
        selected = url_arguments.get("chatbot")
        self.accept()

        if selected not in self.chatbots.keys():
            self.send(
                text_data=json.dumps(
                    {
                        "message": f"Chatbot {selected} not in available chatbots: {self.chatbots.keys()}",
                    }
                )
            )
            self.close(code=400)

        self.chatbot = self.chatbots[selected](id=url_arguments["session"])

        self.send(text_data=json.dumps({"message": "Connected to chatbot"}))

    def disconnect(self, code):
        return None

    # this function receives messages on an opened websocket stream and calls chatbot_main to get teh appropriate engine
    # and sends that back through the socket
    def receive(self, text_data=None, bytes_data=None):
        if not self.chatbot:
            return

        if text_data:
            self.send(text_data=json.dumps({"message": self.chatbot.prompt(text_data)}))
