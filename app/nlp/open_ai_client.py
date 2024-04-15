import os
import openai
from app.nlp.llm_client import LLMClient


class OpenAIClient(LLMClient):
    ''' OpenAI Language Model '''
    def __init__(self):
        initial_prompt = os.environ.get("OPENAI_INITIAL_PROMPT")
        api_key = os.environ.get("OPENAI_API_KEY")
        model_name = os.environ.get("OPENAI_MODEL_NAME")

        self.client = openai.ChatCompletion.create(
            engine=model_name,
            prompt=initial_prompt,
            max_tokens=100,
            api_key=api_key
        )
        super().__init__(initial_prompt)

    def generate_text(self, prompt):
        ''' Generate text based on the prompt'''
        self.client.update(prompt=prompt)
        response = self.client.generate()
        return response.choices[0].message['content']