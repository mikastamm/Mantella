import logging
from typing import Dict
from src.conversation.notification import Notification
from src.llm.message_thread import message_thread
from src.llm.messages import notification_message
from src.http.communication_constants import communication_constants

class notification_manager:


    def __init__(self, get_message_thread: lambda: message_thread) -> None:
        self.__notifications: Dict[str, Notification] = {}
        self.__notification_messages: Dict[str, notification_message] = {}
        self.__get_message_thread: lambda: message_thread = get_message_thread

    def set_notification(self, notification: Notification):
        # Add or update notification
        if(not notification.notification_id in self.__notifications):
            self.__notifications[notification.notification_id] = notification
        else:
            self.__notifications[notification.notification_id].update_notification(notification)

        thread = self.__get_message_thread()
        if not thread:
            logging.error(f"Cannot add Notfication - No message thread found ({notification.notification_id}@{notification.mod_name}: '{notification.text}')")
            return
        
        # add notification to message thread if it doesnt exist
        if(not notification.notification_id in self.__notification_messages):   
            msg =msg(notification.text, notification.mod_name) 
            self.__notification_messages[notification.notification_id] = msg
            self.thread.add_message(msg)

        # remove message from message thread if notification is empty
        if(notification.text == "" and notification.notification_id in self.__notification_messages):
            self.thread.remove_message(self.__notification_messages[notification.notification_id])
        else:
            logging.warning("Tried to remove a notification that does not exist")

        

        