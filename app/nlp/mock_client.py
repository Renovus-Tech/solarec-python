from nlp.llm_client import LLMClient


class MockClient(LLMClient):

    def __init__(self):
        pass

    def generate_text(self, prompt):
        return prompt
