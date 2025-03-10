import json
from src.config.config_loader import ConfigLoader
from src.conversation.action import action


class ActionManager:
    def __init__(self, config:ConfigLoader) -> None:
        self.__config = config
        self.actions = config.__actions
        
    def handle_modify_action_request(self, request_json):
        id = request_json['id']
        enabled = request_json['enabled']
        action = self.get_action(id)
        pathToActionJson = self.__config.get_action_file_path(id)
        # load action file to dict
        with open(pathToActionJson, 'r') as file:
            actionJson = json.load(file)
        # modify action
        actionJson["enabled"] = enabled
        action.enabled = enabled
        # save action file
        with open(pathToActionJson, 'w') as file:
            json.dump(actionJson, file)
        
        
    def get_action(self, action_id:str)->action:
        return [a for a in self.__config.actions if a.identifier == action_id]
        

 