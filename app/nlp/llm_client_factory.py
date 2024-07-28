from app.nlp.gemini_client import GeminiAIClient
from app.nlp.llama_client import LlamaAIClient
from app.nlp.open_ai_client import OpenAIClient


class LLMClientFactory():
    ''' Factory class for creating LLMClient instances'''

    @staticmethod
    def create_llm_client(llm_type: str, initial_prompt: str):
        ''' Create an LLMClient instance based on the type'''

        llm_client_name = os.environ.get("LLM_CLIENT_NAME")
        if llm_client_name == 'geminai':
            return GeminiAIClient(initial_prompt)
        elif llm_client_name == 'openai':
            return OpenAIClient(initial_prompt)
        elif llm_client_name == 'llama':
            return LlamaAIClient(initial_prompt)
        else:
            raise ValueError(f"Invalid LLM client name: {llm_client_name}")
