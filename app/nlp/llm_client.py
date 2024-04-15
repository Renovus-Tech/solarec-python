from abc import abstractmethod
import json

class LLMClient():
    ''' Base class for Language Model'''

    @abstractmethod
    def __init__(self, initial_prompt):
        ''' Initialize the Language Model with an initial prompt'''
        self.initial_prompt = initial_prompt

    @abstractmethod
    def generate_text(self, prompt):
        ''' Generate text based on the prompt'''
        pass

    def generate_json(self, prompt) -> dict:
        ''' Generate JSON based on the prompt'''
        return json.loads(self.generate_text(prompt))