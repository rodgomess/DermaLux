import requests
from dotenv import load_dotenv
import os


class ZApi():
    def __init__(self):
        load_dotenv()
        self.INSTANCE_API = os.getenv('INSTANCE_API')
        self.SECURITY_TOKEN = os.getenv('SECURITY_TOKEN')

    def send_message(self, phone, message):
        url = self.INSTANCE_API + "/send-text"
        headers = {
            "Content-Type": "application/json",
            "Client-Token": self.SECURITY_TOKEN
        }

        body = {
            'phone': phone,
            'message': message
        }
        
        r = requests.post(url, json=body, headers=headers)

        return r

    def send_button_message(self, phone, message, buttons):
        url = self.INSTANCE_API + "/send-button-list"
        headers = {
            "Content-Type": "application/json",
            "Client-Token": self.SECURITY_TOKEN
        }

        body = {
            'phone': phone,
            'message': message,
            "buttonList": buttons
        }
        
        r = requests.post(url, json=body, headers=headers)

        return r

    def get_queue(self):
        url = self.INSTANCE_API + "/queue"

        headers = {
            "accept": "application/json",
            "client-token": self.SECURITY_TOKEN
        }

        return requests.get(url, headers=headers)