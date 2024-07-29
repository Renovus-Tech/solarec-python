import os

import google.generativeai as genai

from app.nlp.llm_client import LLMClient


class GeminiAIClient(LLMClient):
    ''' Gemini Language Model '''

    def __init__(self):
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        gemini_model_name = os.environ.get("GEMINI_MODEL_NAME")
        initial_prompt = os.environ.get("GEMINI_INITIAL_PROMPT")

        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(gemini_model_name,   system_instruction=initial_prompt)

    def generate_text(self, prompt):
        ''' Generate text based on the prompt'''
        return self.model.generate_content(prompt)
