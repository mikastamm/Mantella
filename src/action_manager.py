import json
from typing import Callable
from src.conversation.conversation_type import conversation_type, pc_to_npc, multi_npc, radiant
from src.config.config_loader import ConfigLoader
from src.conversation.action import action
from src.utils import utils


class ActionManager:
    
    def __init__(self, config:ConfigLoader, get_conversation_type: Callable[[], conversation_type]):
        self.get_conversation_type: Callable[[], conversation_type] = get_conversation_type
        self.__config = config
        # Ids / names of the sets that are enabled
        self.__enabled_sets = set()
        
        
    def ResetEnabledSets(self):
        self.__enabled_sets.clear()
        
    @utils.time_it
    def GetAvailableActions(self):
        conversation_type = self.get_conversation_type()
        toggledActions = [a for a in self.__config.actions if a.action_set == "" or a.action_set in self.__enabled_sets] 
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
    def GetAvailableActionsText(self, actions: list[action]) -> str:
        """Generates the prompt text for the available actions

        Args:
            actions (list[action]): the list of possible actions. Already filtered for conversation type and config choices

        Returns:
            str: the text for the {actions} variable
        """
        result = ""
        for a in self.GetAvailableActions():
            result += a.prompt_text.format(key=a.keyword) + " "
        return result
            
    def get_action(self, action_id:str)->action:
        return [a for a in self.__config.actions if a.identifier == action_id]
        

 