from fbchat import log, Client, ThreadType
from fbchat.models import MessageReaction, User, Message, TypingStatus
from firebase import firebase
import time
import os


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
    USER_NOT_LOGGED_IN = "@{name} has not logged in. Goto https://hackathon-scheduler.herokuapp.com/authorize/google/ and sign in. @Chronomatch Bot me when this has been completed"

    def onPollUpdated(self, options):
        print("please", maybe_finalize_meeting(options, filter(lambda u: u.uid != self.uid, self.fetchAllUsers())))


    def onMessage(self, mid=None, author_id=None, message=None, message_object=None, thread_id=None,
                  thread_type=ThreadType.USER, ts=None, metadata=None, msg=None):
        print("I have problems", message_object.text or "shit")
        self.markAsDelivered(author_id, thread_id)
        self.markAsRead(author_id)


        if '@Chronomatch Bot' in message_object.text and author_id != self.uid:
            #self.setTypingStatus(TypingStatus.TYPING, thread_id, thread_type)

            #self.send(Message(ScheduleBot.WELCOME), thread_id, thread_type)
            # check all user are in firebase
            # remove bot
            us = filter(lambda u: u.uid != self.uid, self.fetchAllUsers())

            print("us is", us)
            #notloggedin =  (us)
            print("here")
            #print(notloggedin)
            createPole(["It", "Works"])
        #self.setTypingStatus(TypingStatus.STOPPED, thread_id, thread_type)


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
    userList = []
    f = firebase.FirebaseApplication('https://schedule-03022018.firebaseio.com/', None)
    for user in users:
        uid = user.uid
        u = f.get('/user', uid)
        if u is  None:
            userList.append(user)
    return userList

def createPole(options):
    #options is list of strings
    arguments = '"' + '" "'.join(options) + '"' ## TODO: Much hacky

    command = 'npm run start ' + arguments

    os.system(command)

if __name__ == '__main__':
    client = ScheduleBot("dorota.test1@gmail.com", "b35tt3am")
    client.listen()
