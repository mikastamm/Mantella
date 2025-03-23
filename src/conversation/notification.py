from src.http.communication_constants import communication_constants


class Notification:
    def __init__(self, modName:str, notificationId:str, text:str):
        self.mod_name = modName
        self.notification_id = notificationId
        self.text = text

    def update_notification(self, notification: 'Notification'):
        self.text = notification.text
        self.mod_name = notification.mod_name
        self.notification_id = notification.notification_id

    @staticmethod
    def from_json(json):
        return Notification(json[communication_constants.KEY_NOTIFICATION_SOURCE], 
                            json[communication_constants.KEY_NOTIFICATION_ID], 
                            json[communication_constants.KEY_NOTIFICATION_MESSAGE])