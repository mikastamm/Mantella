from calendar import c
import json
from typing import Callable, Dict
from src.actions.action_accessor import ActionAccessor
from src.conversation.conversation_type import conversation_type, pc_to_npc, multi_npc, radiant
from src.config.config_loader import ConfigLoader
from src.conversation.action import action
from src import utils
from src.http.communication_constants import communication_constants



class ActionManager(ActionAccessor):
    """ 
    Repository for the available actions. You can define actions through json files in Data/Actions. By default actions are always available.
    
    You can associate actions with an action_set. This makes them disabled by default, needing you to enable them first. 
    
    Send KEY_REQUESTTYPE_TOGGLE_ACTION_SET to the mantella endpoint to enable / disable all actions in that action-set.  Body:
    {
        "action_set": str,
        "enabled": bool
    }
    
    Note: To keep the game and server in sync, action sets are always disabled at the start of the conversation. 
    In your plugin, you have to respond to the conversation start event and decide weather to enable your action set or not.
    """
    
    
    def __init__(self, config:ConfigLoader, get_conversation_type: Callable[[], conversation_type]):
        self.get_conversation_type: Callable[[], conversation_type] = get_conversation_type
        self.__config = config
        # Ids / names of the sets that are enabled
        self.__enabled_sets = set()
        
        
    def ResetEnabledSets(self):
        self.__enabled_sets.clear()
    
    def handle_toggle_action_set_request(self, json:Dict[str, any]):
        """ Enables or disables all actions, which are tagged with the given action_set"""
        enable:bool = json[communication_constants.KEY_ACTION_SET_ENABLED]
        action_set:str = json[communication_constants.KEY_ACTION_SET_ID]
        if enable and action_set:
            self.__enabled_sets.add(action_set.lower())
        else:
            self.__enabled_sets.remove(action_set.lower())
        return  {communication_constants.KEY_REPLYTYPE: communication_constants.KEY_REPLYTYPE_TOGGLE_ACTION_SET}
        
    @utils.time_it
    def GetAvailableActions(self):
        conversation_type = self.get_conversation_type()
        toggledActions = [a for a in self.__config.actions if a.action_set == "" or a.action_set.lower() in self.__enabled_sets] 
        available = []
        for a in toggledActions:
            if a.use_in_multi_npc and isinstance(conversation_type, multi_npc):
                available.append(a) 
            elif a.use_in_on_on_one and isinstance(conversation_type, pc_to_npc):
                available.append(a)
            elif a.use_in_radiant and isinstance(conversation_type, radiant):    
                available.append(a) 
        return available
    
    @utils.time_it
    def GetAvailableActionsText(self) -> str:
        result = ""
        for a in self.GetAvailableActions():
            result += a.prompt_text.format(key=a.keyword) + " "
        return result
            
    def get_action(self, action_id:str)->action:
        return [a for a in self.__config.actions if a.identifier == action_id]
        

 