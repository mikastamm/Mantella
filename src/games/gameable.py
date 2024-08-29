from abc import ABC, abstractmethod
import json
import logging
import os
from pathlib import Path
from typing import Any
import pandas as pd
from src.conversation.conversation_log import conversation_log
from src.conversation.context import context
from src.config.config_loader import ConfigLoader
from src.llm.sentence import sentence
from src.games.external_character_info import external_character_info
import src.utils as utils

class gameable(ABC):
    """Abstract class for different implementations of games to support. 
    Make a subclass for every game that Mantella is supposed to support and implement this interface
    Anything that is specific to a certain game should end up in one of these subclasses.
    If there are new areas where a game specific handling is required, add new methods to this and implement them in all of the subclasses

    Args:
        ABC (_type_): _description_
    """
    def __init__(self, config: ConfigLoader, path_to_character_df: str, mantella_game_folder_path: str):
        try:
            self.__character_df: pd.DataFrame = self.__get_character_df(path_to_character_df)
        except:
            logging.error(f'Unable to read / open {path_to_character_df}. If you have recently edited this file, please try reverting to a previous version. This error is normally due to using special characters, or saving the CSV in an incompatible format.')
            input("Press Enter to exit.")

        #Apply character overrides
        mod_overrides_folder = os.path.join(*[config.mod_path_base,"SKSE","Plugins","MantellaSoftware","data",f"{mantella_game_folder_path}","character_overrides"])
        self.__apply_character_overrides(mod_overrides_folder, self.__character_df.columns.values.tolist())
        personal_overrides_folder = os.path.join(config.save_folder, f"data/{mantella_game_folder_path}/character_overrides")     
        self.__apply_character_overrides(personal_overrides_folder, self.__character_df.columns.values.tolist())

        self.__conversation_folder_path = config.save_folder + f"data/{mantella_game_folder_path}/conversations"
        
        conversation_log.game_path = self.__conversation_folder_path
    
    @property
    def character_df(self) -> pd.DataFrame:
        return self.__character_df
    
    @property
    def conversation_folder_path(self) -> str:
        return self.__conversation_folder_path
    
    def __get_character_df(self, file_name: str) -> pd.DataFrame:
        encoding = utils.get_file_encoding(file_name)
        character_df = pd.read_csv(file_name, engine='python', encoding=encoding)

        return character_df
    
    @abstractmethod
    def load_external_character_info(self, base_id: str, name: str, race: str, gender: int, actor_voice_model_name: str)-> external_character_info:
        """This loads extra information about a character that can not be gained from the game. i.e. bios or voice_model_names for TTS

        Args:
            id (str): the id of the character to get the extra information from
            name (str): the name of the character to get the extra information from
            race (str): the race of the character to get the extra information from
            gender (int): the gender of the character to get the extra information from
            actor_voice_model_name (str): the ingame voice model name of the character to get the extra information from

        Returns:
            external_character_info: the missing information
        """
        pass    

    @abstractmethod
    def prepare_sentence_for_game(self, queue_output: sentence, context_of_conversation: context, config: ConfigLoader):
        """Does what ever is needed to play a sentence ingame

        Args:
            queue_output (sentence): the sentence to play
            context_of_conversation (context): the context of the conversation
            config (ConfigLoader): the current config
        """
        pass

    @abstractmethod
    def is_sentence_allowed(self, text: str, count_sentence_in_text: int) -> bool:
        """Checks a sentence generated by the LLM for game specific stuff

        Args:
            text (str): the sentence text to check
            count_sentence_in_text (int): count of sentence in text

        Returns:
            bool: True if sentence is allowed, False otherwise
        """
        pass

    @abstractmethod
    def load_unnamed_npc(self, name: str, actor_race: str, actor_sex: int, ingame_voice_model:str) -> dict[str, Any]:
        """Loads a generic NPC if the NPC is not found in the CSV file

         Args:
            name (str): the name of the character
            race (str): the race of the character
            gender (int): the gender of the character
            ingame_voice_model (str): the ingame voice model name of the character

        Returns:
            dict[str, Any]: A dictionary containing NPC info (name, bio, voice_model, advanced_voice_model, voice_folder)
        """
        pass

    @abstractmethod
    def get_weather_description(self, weather_attributes: dict[str, Any]) -> str:
        """Returns a description of the current weather that can be used in the prompts

        Args:
            weather_attributes (dict[str, Any]): The json of weather attributes as transferred by the respective game

        Returns:
            str: A prose description of the weather for the LLM
        """
        pass

    @abstractmethod
    def find_best_voice_model(self, actor_race: str, actor_sex: int, ingame_voice_model: str) -> str:
        """Returns the voice model which most closely matches the NPC

        Args:
            actor_race (str): The race of the NPC
            actor_sex (int): The sex of the NPC
            ingame_voice_model (str): The in-game voice model provided for the NPC

        Returns:
            str: The voice model which most closely matches the NPC
        """
        pass

    def _get_matching_df_rows_matcher(self, base_id: str, character_name: str, race: str) -> pd.Series | None:
         # TODO: try loading the NPC's voice model as soon as the NPC is found to speed up run time and so that potential errors are raised ASAP
        full_id_len = 6
        full_id_search = base_id[-full_id_len:].lstrip('0')  # Strip leading zeros from the last 6 characters

        # Function to remove leading zeros from hexadecimal ID strings
        def remove_leading_zeros(hex_str):
            if pd.isna(hex_str):
                return ''
            return str(hex_str).lstrip('0')

        id_match = self.character_df['base_id'].apply(remove_leading_zeros).str.lower() == full_id_search.lower()
        name_match = self.character_df['name'].astype(str).str.lower() == character_name.lower()

        # character_race = race.split('<')[1].split('Race ')[0] # TODO: check if this covers "character_currentrace.split('<')[1].split('Race ')[0]" from FO4
        # race_match = self.character_df['race'].astype(str).str.lower() == character_race.lower()
        race_match = self.character_df['race'].astype(str).str.lower() == race.lower()

        # Partial ID match with decreasing lengths
        partial_id_match = pd.Series(False, index=self.character_df.index)
        for length in [5, 4, 3]:
            if partial_id_match.any():
                break
            partial_id_search = base_id[-length:].lstrip('0')  # strip leading zeros from partial ID search
            partial_id_match = self.character_df['base_id'].apply(
                lambda x: remove_leading_zeros(str(x)[-length:]) if pd.notna(x) and len(str(x)) >= length else remove_leading_zeros(str(x))
            ).str.lower() == partial_id_search.lower()

        is_generic_npc = False

        ordered_matchers = {
            'name, ID, race': name_match & id_match & race_match, # match name, full ID, race (needed for Fallout 4 NPCs like Curie)
            'name, ID': name_match & id_match, # match name and full ID
            'name, partial ID, race': name_match & partial_id_match & race_match, # match name, partial ID, and race
            'name, partial ID': name_match & partial_id_match, # match name and partial ID
            'name, race': name_match & race_match, # match name and race
            'name': name_match, # match just name
            'ID': id_match # match just ID
        }

        for matcher in ordered_matchers:
            view = self.character_df.loc[ordered_matchers[matcher]]
            if view.shape[0] == 1: #If there is exactly one match
                logging.info(f'Matched {character_name} in CSV by {matcher}')
                return ordered_matchers[matcher]
            
        return None
        # try: # match name, full ID, race (needed for Fallout 4 NPCs like Curie)
        #     logging.info(" # match name, full ID, race (needed for Fallout 4 NPCs like Curie)")
        #     return self.character_df.loc[name_match & id_match & race_match]
        # except IndexError:
        #     try: # match name and full ID
        #         logging.info(" # match name and full ID")
        #         return self.character_df.loc[name_match & id_match]
        #     except IndexError:
        #         try: # match name, partial ID, and race
        #                 logging.info(" # match name, partial ID, and race")
        #                 return self.character_df.loc[name_match & partial_id_match & race_match]
        #         except IndexError:
        #             try: # match name and partial ID
        #                 logging.info(" # match name and partial ID")
        #                 return self.character_df.loc[name_match & partial_id_match]
        #             except IndexError:
        #                 try: # match name and race
        #                     logging.info(" # match name and race")
        #                     return self.character_df.loc[name_match & race_match]
        #                 except IndexError:
        #                     try: # match just name
        #                         logging.info(" # match just name")
        #                         return self.character_df.loc[name_match]
        #                     except IndexError:
        #                         try: # match just ID
        #                             logging.info(" # match just ID")
        #                             return self.character_df.loc[id_match]
        #                         except IndexError: # treat as generic NPC
        #                             logging.info(f"Could not find {character_name} in skyrim_characters.csv. Loading as a generic NPC.")
        #                             return pd.DataFrame()

    def find_character_info(self, base_id: str, character_name: str, race: str, gender: int, ingame_voice_model: str):
        character_race = race.split('<')[1].split('Race ')[0] # TODO: check if this covers "character_currentrace.split('<')[1].split('Race ')[0]" from FO4
        matcher = self._get_matching_df_rows_matcher(base_id, character_name, character_race)
        if isinstance(matcher, type(None)):
            logging.info(f"Could not find {character_name} in skyrim_characters.csv. Loading as a generic NPC.")
            character_info = self.load_unnamed_npc(character_name, character_race, gender, ingame_voice_model)
            is_generic_npc = True
        else:
            result = self.character_df.loc[matcher]
            character_info = result.to_dict('records')[0]
            if (character_info['voice_model'] is None) or (pd.isnull(character_info['voice_model'])) or (character_info['voice_model'] == ''):
                character_info['voice_model'] = self.find_best_voice_model(race, gender, ingame_voice_model) 
            is_generic_npc = False                                   

        return character_info, is_generic_npc
    
    def __apply_character_overrides(self, overrides_folder: str, character_df_column_headers: list[str]):
        if not os.path.exists(overrides_folder):
            os.makedirs(overrides_folder)
        override_files: list[str] = os.listdir(overrides_folder)
        for file in override_files:
            try:
                filename, extension = os.path.splitext(file)
                full_path_file = os.path.join(overrides_folder,file)
                if extension == ".json":
                    with open(full_path_file) as fp:
                        json_object = json.load(fp)
                        if isinstance(json_object, dict):#Otherwise it is already a list
                            json_object = [json_object]
                        for json_content in json_object:
                            content: dict[str, str] = json_content
                            name = content.get("name", "")
                            base_id = content.get("base_id", "")
                            race = content.get("race", "")
                            matcher = self._get_matching_df_rows_matcher(base_id, name, race)
                            if isinstance(matcher, type(None)): #character not in csv, add as new row
                                row = []
                                for entry in character_df_column_headers:
                                    value = content.get(entry, "")
                                    row.append(value)
                                self.character_df.loc[len(self.character_df.index)] = row
                            else: #character is in csv, update row
                                for entry in character_df_column_headers:
                                    value = content.get(entry, None)
                                    if value and value != "":
                                        self.character_df.loc[matcher, entry] = value
                elif extension == ".csv":
                    extra_df = self.__get_character_df(full_path_file)
                    for i in range(extra_df.shape[0]):#for each row in df
                        name = extra_df.iloc[i].get("name", "")
                        base_id = extra_df.iloc[i].get("base_id", "")
                        race = extra_df.iloc[i].get("race", "")
                        matcher = self._get_matching_df_rows_matcher(base_id, name, race)
                        if isinstance(matcher, type(None)): #character not in csv, add as new row
                            row = []
                            for entry in character_df_column_headers:
                                value = extra_df.iloc[i].get(entry, "")
                                row.append(value)
                            self.character_df.loc[len(self.character_df.index)] = row
                        else: #character is in csv, update row
                            for entry in character_df_column_headers:
                                value = extra_df.iloc[i].get(entry, None)
                                if value and not pd.isna(value) and value != "":
                                    self.character_df.loc[matcher, entry] = value
            except Exception as e:
                logging.log(logging.WARNING, f"Could not load character override file '{file}' in '{overrides_folder}'. Most likely there is an error in the formating of the file. Error: {e}")

        
