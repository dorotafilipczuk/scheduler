import os

from flask import Flask, Response, request


app = Flask(__name__)


@app.route('/')
def index():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/callback')
def google_auth_callback():
    """
    Route used by google to authenticate a user
    """
    pass


if __name__ == '__main__':
    app.run()
