from datetime import datetime
import json
import os
import sys

from dotenv import load_dotenv
from flask import Flask, request, current_app, url_for, redirect, jsonify
import requests
from rauth import OAuth2Service

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


class Config(object):
    OAUTH_CREDENTIALS = {
        'google': {
            'id': os.environ['GOOGLE_ID'],
            'secret': os.environ['GOOGLE_SECRET']
        }
    }


class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']
        self.scope = ''

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', provider=self.provider_name,
                       _external=True)

    @classmethod
    def get_provider(self, provider_name):
        """

        Args:
            provider_name (str): The name of the provider

        Returns:
            OAuthSignIn: A subclass of OAuthSignIn

        """
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class GoogleSignIn(OAuthSignIn):
    def __init__(self):
        super(GoogleSignIn, self).__init__('google')
        self.service = OAuth2Service(
            name='google',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://accounts.google.com/o/oauth2/auth',
            access_token_url='https://accounts.google.com/o/oauth/token',
            base_url='https://www.googleapis.com/calendar/v3'
        )
        self.scope = 'https://www.googleapis.com/auth/calendar'

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope=self.scope,
            response_type='code',
            redirect_uri=self.get_callback_url()
        ))

    def callback(self):
        def decode_json(payload):
            return json.loads(payload.decode('utf-8'))
        error = request.args.get('error')
        if error is not None:
            pass  # User did not give us access

        code = request.args.get('code')

        session = self.service.get_auth_session(
            data={'code': code,
                   'grant_type': 'authorization_code',
                   'redirect_uri': self.get_callback_url()
                    },
            decoder=json.loads
        )

        temp = session.get('https://www.googleapis.com/calendar/v3/users/me/calendarList').json()
        print(temp)



app = Flask(__name__)
app.config.from_object(Config())


@app.route('/callback/<provider>/')
def oauth_callback(provider):
    """
    Route used by google to authenticate a user
    """
    oauth = OAuthSignIn.get_provider(provider)
    oauth.callback()
    return jsonify({'data': oauth.session.request('/users/me/calendarList')})


@app.route('/authorize/<string:provider>/')
def authorize(provider):
    # TODO: Check user is already signed in
    oauth = OAuthSignIn.get_provider(provider)  # TODO: Other calendar providers
    return oauth.authorize()


@app.route('/', methods=['GET'])
def index():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    # FIXME testing code
    send_message(sender_id, json.dumps(data))
    return "ok", 200



    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    send_message(sender_id, json.dumps(data))

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text,
            "quick_replies":[
            {
              "content_type":"text",
              "title":"BUTTON_TEXT",
              "image_url":"http://example.com/img/red.png",
              "payload":"STRING_SENT_TO_WEBHOOK"
            }]
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(msg, *args, **kwargs):  # simple wrapper for logging to stdout on heroku
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        else:
            msg = str(msg).format(*args, **kwargs)
        print(u"{}: {}".format(datetime.now(), msg))
    except UnicodeEncodeError:
        pass  # squash logging errors in case of non-ascii text
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
