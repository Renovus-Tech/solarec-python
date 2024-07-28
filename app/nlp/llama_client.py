import os

import google.generativeai as genai
from openai import OpenAI

from app.nlp.llm_client import LLMClient


class LlamaAIClient(LLMClient):
    ''' Gemini Language Model '''

    def __init__(self):
        api_key = os.environ.get("LLAMA_API_KEY")
        base_url = os.environ.get("LLAMA_BASE_URL")
        self.model_name = os.environ.get("LLAMA_MODEL_NAME")
        self.initial_prompt = os.environ.get("LLAMA_INITIAL_PROMPT")

        self.client = OpenAI(api_key=api_key, base_url=base_url)


def generate_text(self, prompt):
    ''' Generate text based on the prompt'''
    response = self.client.chat.completions.create(
        model=self.model_name, messages=[
            {"role": "system", "content": self.initial_prompt},
            {"role": "user", "content": prompt}])

    response_json = response.model_dump_json(indent=2)
    return response_json.choices[0].message.content
