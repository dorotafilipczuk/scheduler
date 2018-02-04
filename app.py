from datetime import datetime
import json
from pprint import pprint
import os
import re
import sys

from dotenv import load_dotenv
from flask import Flask, request, current_app, url_for, redirect, jsonify
import requests
from rauth import OAuth2Service

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

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
        self.session = None

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
            access_token_url='https://accounts.google.com/o/oauth2/token',
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
        error = request.args.get('error')
        if error is not None:
            pass  # User did not give us access

        code = request.args.get('code')

        self.session = self.service.get_auth_session(
            data={'code': code,
                   'grant_type': 'authorization_code',
                   'redirect_uri': self.get_callback_url()
                    },
            decoder=json.loads
        )


app = Flask(__name__)
app.config.from_object(Config())


@app.route('/callback/<provider>/')
def oauth_callback(provider):
    """
    Route used by google to authenticate a user
    """
    oauth = OAuthSignIn.get_provider(provider)
    oauth.callback()
    response = oauth.session.get('https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={}&singleEvents=true'.format(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))).json()

    calendar_events = []

    if response.get('kind', '') == 'calendar#events':
        for item in response['items']:
            print(item)
            event = {}
            try:
                event['start'] = item['start']['date']
                if DATE_REGEX.fullmatch(event['start']) is not None:
                    # Its a date
                    event['start'] = event['start'] + 'T00:00:00Z'
                event['end'] = item['end']['date']
                if DATE_REGEX.fullmatch(event['end']) is not None:
                    # Its a date
                    event['end'] = event['end'] + 'T23:59:59Z'


            except KeyError:
                event['start'] = item['start']['dateTime']
                if DATE_REGEX.fullmatch(event['start']) is not None:
                    # Its a date
                    event['start'] = event['start'] + 'T00:00:00Z'
                event['end'] = item['end']['dateTime']
                if DATE_REGEX.fullmatch(event['end']) is not None:
                    # Its a date
                    event['end'] = event['end'] + 'T23:59:59Z'
            calendar_events.append(event)

    return jsonify({'events': calendar_events}) #### Use the dict inside the parenthesis for dict


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
    get_options()
    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

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

def sort_by_start_time(d):
    return d["start"]

def get_options():
    data = []
    for event in json.load(open('test_data/user1.json'))["events"]:
        data.append(event)
    for event in json.load(open('test_data/user2.json'))["events"]:
        data.append(event)
    now = datetime.now()

    sorted_data = sorted(data, key=sort_by_start_time)

    data = []
    for event in sorted_data:
        end = datetime.strptime(event["end"], "%Y-%m-%dT%H:%M:%SZ")
        print(type(end))
        if end > now:
            data.append(event)

    options = []
    event1 = data[0]
    i = 1
    while i < len(data):
        event2 = data[i]
        end1 = event1["end"]
        end2 = event2["end"]
        start1 = event1["start"]
        start2 = event2["start"]

        if end2 > end1:
            if start2 <= end1:
                event1["end"] = end2
            else:
                options.append(end1)
                event1 = event2

        # TODO(dorotafilipczuk): Make sure that there are no options after
        # 22:00. Add morning event options.

        i += 1

    return options

def format_options(options):
    length = len(options)
    if length > 11:
        length = 11

    #TODO(dorotafilipczuk): If length < 1, throw an exception.

    reformatted = []
    i = 0;
    while i < length:
        print(options[i])
        o = datetime.strptime(options[i], "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M on %d %b %Y")
        reformatted.append(o)
        i += 1

    return reformatted

def get_quick_replies():
    quick_replies = []
    options = get_options()
    reformatted = format_options(options)
    for option in reformatted:
        quick_replies.append({
          "content_type":"text",
          "title": option,
          "payload":"STRING_SENT_TO_WEBHOOK"
        })

    return quick_replies


def send_message(recipient_id, message_text):

    #log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    quick_replies = get_quick_replies()

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
            "quick_replies": quick_replies
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
