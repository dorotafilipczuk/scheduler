from fbchat import log, Client, ThreadType
from fbchat.models import MessageReaction


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
    def onMessage(self, mid=None, author_id=None, message=None, message_object=None, thread_id=None,
                  thread_type=ThreadType.USER, ts=None, metadata=None, msg=None):
        self.markAsDelivered(author_id, thread_id)
        self.markAsRead(author_id)

        if message_object:
            pass # TODO



if __name__ == '__main__':
    client = EchoBot("dorota.test1@gmail.com", "b35tt3am")
    client.listen()