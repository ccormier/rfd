import requests

class PushOver:
    def __init__(self, app_token, user_key):
        self.app_token = app_token
        self.user_key = user_key

    def send_message(self, message, title=None, url=None):
        data = {"token": self.app_token,
                "user": self.user_key,
                "message": message}
        if title:
            data["title"] = title
        if url:
            data["url"] = url

        r = requests.post("https://api.pushover.net/1/messages.json", data = data, headers = {
                "Content-type": "application/x-www-form-urlencoded"
            })

    def send_image(self, file):
        r = requests.post("https://api.pushover.net/1/messages.json", data = {
            "token": self.app_token,
            "user": self.user_key,
            "message": "hello world"
        }, files = {
            "attachment": ("image.jpg", open(file, "rb"), "image/jpeg")
            })

