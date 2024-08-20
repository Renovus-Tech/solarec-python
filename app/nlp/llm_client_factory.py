import os

from nlp.gemini_client import GeminiAIClient
from nlp.llama_client import LlamaAIClient
from nlp.openai_client import OpenAIClient
from nlp.mock_client import MockClient


class LLMClientFactory():
    ''' Factory class for creating LLMClient instances'''

    @staticmethod
    def create_llm_client():
        ''' Create an LLMClient instance based on the type'''

        llm_client_name = os.environ.get("LLM_CLIENT_NAME")
        if llm_client_name == 'geminai':
            return GeminiAIClient()
        elif llm_client_name == 'openai':
            return OpenAIClient()
        elif llm_client_name == 'llama':
            return LlamaAIClient()
        elif llm_client_name == 'mock':
            return MockClient()
        else:
            raise ValueError(f"Invalid LLM client name: {llm_client_name}")
