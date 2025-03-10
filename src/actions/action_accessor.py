from src.conversation.action import action


class ActionAccessor():
    """Interface for the ActionManager to get available actions
    """
    def GetAvailableActions(self) -> list[action]:
        pass
    
    """Generates the prompt text for the available actions

    Args:
        actions (list[action]): the list of possible actions. Already filtered for conversation type and config choices

    Returns:
        str: the text for the {actions} variable
    """
    def GetAvailableActionsText(self) -> str:
        pass    