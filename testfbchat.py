from fbchat import log, Client, ThreadType
from fbchat.models import MessageReaction, User, Message, TypingStatus
from firebase import firebase
import time
import os
from app import *


# Subclass fbchat.Client and override required methods
# class EchoBot(Client):
#     def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
#         self.markAsDelivered(author_id, thread_id)
#         self.markAsRead(author_id)
#
#         log.info("{} from {} in {}".format(message_object, thread_id, thread_type.name))
#
#
#         # If you're not the author, echo
#         if author_id != self.uid:
#             messageid = self.send(message_object, thread_id=thread_id, thread_type=thread_type)


class ScheduleBot(Client):
    """


    """

    WELCOME = "I am here to assist you. I'll help you schedule a meeting!"
    USER_NOT_LOGGED_IN = "{name} has not logged in. Goto URL and sign in. Mention me when this has been completed"

    def sort_by_start_time(self, d):
        return d["start"]

    def get_options(self, data):
        now = datetime.now()

        sorted_data = sorted(data, key=self.sort_by_start_time)

        data = []
        for event in sorted_data:
            end = datetime.strptime(event["end"], "%Y-%m-%dT%H:%M:%SZ")
            # print(type(end))
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

    def format_options(self, options):
        length = len(options)
        if length > 5:
            length = 5

        #TODO(dorotafilipczuk): If length < 1, throw an exception.

        reformatted = []
        i = 0
        while i < length:
            # print(options[i])
            o = datetime.strptime(options[i], "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M on %d %b %Y")
            reformatted.append(o)
            i += 1

        return reformatted

    def onPollUpdated(self, options, poll_id):
        print("please", maybe_finalize_meeting(options, filter(lambda u: u.uid != self.uid, self.fetchAllUsers())))


    def onMessage(self, mid=None, author_id=None, message=None, message_object=None, thread_id=None,
                  thread_type=ThreadType.USER, ts=None, metadata=None, msg=None):

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
            #print(calendar_events)
            options = self.format_options(self.get_options(calendar_events))


            createPole(options)
        self.setTypingStatus(TypingStatus.STOPPED, thread_id, thread_type)


def maybe_finalize_meeting(poll_opts, all_users):
    best_option = poll_opts[0]
    users_voted = []
    for option in poll_opts:
        if option["total_count"] > best_option["total_count"]:
            best_option = option
        users_voted = list(set().union(users_voted, option["voters"]))
    print ("best match is ", best_option)
    print("users voted", users_voted)
    return set(all_users) == set(users_voted)


def users_logged_in(users):
    db = firebase.FirebaseApplication('https://schedule-03022018.firebaseio.com/', None)
    userList = []
    f = firebase.FirebaseApplication('https://schedule-03022018.firebaseio.com/', None)
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
