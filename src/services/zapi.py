import requests
import os


class ZApi():
    def __init__(self):
        self.INSTANCE_API = os.getenv('INSTANCE_API')
        self.INSTANCE_TOKEN = os.getenv('INSTANCE_TOKEN')
        self.INSTANCE_ID = os.getenv('INSTANCE_ID')
        self.SECURITY_TOKEN = os.getenv('SECURITY_TOKEN')

    def send_message(self, phone, message):
        headers = {
            "Content-Type": "application/json",
            "Client-Token": self.SECURITY_TOKEN
        }

        body = {
            'phone': phone,
            'message': message
        }
        
        r = requests.post(self.INSTANCE_API, json=body, headers=headers)

        return r

    def get_queue(self):

        url = f"https://api.z-api.io/instances/{self.INSTANCE_ID}/token/{self.INSTANCE_TOKEN}/queue"

        headers = {
            "accept": "application/json",
            "client-token": self.SECURITY_TOKEN
        }

        return requests.get(url, headers=headers)