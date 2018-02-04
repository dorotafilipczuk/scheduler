from fbchat import log, Client, ThreadType
from fbchat.models import MessageReaction, User, Message, TypingStatus
from firebase import firebase
import time
import os
from app import *


# Subclass fbchat.Client and override required methods
class EchoBot(Client):
    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        self.markAsDelivered(author_id, thread_id)
        self.markAsRead(author_id)

        log.info("{} from {} in {}".format(message_object, thread_id, thread_type.name))


        # If you're not the author, echo
        if author_id != self.uid:
            messageid = self.send(message_object, thread_id=thread_id, thread_type=thread_type)


class ScheduleBot(Client):
    """


    """

    WELCOME = "I am here to assist you. I'll help you schedule a meeting!"
    USER_NOT_LOGGED_IN = "{name} has not logged in. Goto URL and sign in. Mention me when this has been completed"

    def onMessage(self, mid=None, author_id=None, message=None, message_object=None, thread_id=None,
                  thread_type=ThreadType.USER, ts=None, metadata=None, msg=None):
        print("New Message: ", message_object)
        self.markAsDelivered(author_id, thread_id)
        self.markAsRead(author_id)

        if '@Chronomatch Bot' in message_object.text and author_id != self.uid:
            self.setTypingStatus(TypingStatus.TYPING, thread_id, thread_type)

            self.send(Message(ScheduleBot.WELCOME), thread_id, thread_type)
            # check all user are in firebase
            # remove bot
            us = list(filter(lambda u: u.uid != self.uid, self.fetchAllUsers()))

            notloggedin = users_logged_in(us)
            print(notloggedin)

            if len(notloggedin) != 0:
                for user in notloggedin:
                    m = Message(ScheduleBot.USER_NOT_LOGGED_IN.format(name=user.name))

                    self.send(m, thread_id=thread_id, thread_type=thread_type)
                    time.sleep(0.2)
                return

            calendar_events = []
            tokens = get_tokens(us)
            for t in tokens:
                signin = GoogleSignIn()
                response = signin.service.get_session(token=t).get('https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={}&singleEvents=true'.format(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))).json()
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
            print(calendar_events)
            createPole(["It", "Works"])
        self.setTypingStatus(TypingStatus.STOPPED, thread_id, thread_type)


def users_logged_in(users):
    db = firebase.FirebaseApplication('https://schedule-03022018.firebaseio.com/', None)
    userList = []
    for user in users:
        uid = user.uid
        u = db.get('/user', uid)
        if u is  None:
            userList.append(user)
    return userList

def get_tokens(users):
    db = firebase.FirebaseApplication('https://schedule-03022018.firebaseio.com/', None)
    tokenList = []
    for user in users:
        uid = user.uid
        u = db.get('/user', uid)
        tokenList.append(u)
    return tokenList

def createPole(options):
    #options is list of strings
    arguments = '"' + '" "'.join(options) + '"' ## TODO: Much hacky

    command = 'npm run start ' + arguments

    os.system(command)

if __name__ == '__main__':
    client = ScheduleBot("dorota.test1@gmail.com", "b35tt3am")
    client.listen()
