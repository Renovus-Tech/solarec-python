from unittest.mock import patch

from app.nlp.llm_client_factory import LLMClientFactory
from app.nlp.onboarding_helper import NLPOnboardingHelper


def test_get_llm_client_gemini():
    with patch('app.nlp.llm_client_factory.os') as mock_os:
        mock_os.environ.get.return_value = 'geminai'

        with patch('app.nlp.llm_client_factory.GeminiAIClient') as mock_gemini_client:
            llm_client = LLMClientFactory.create_llm_client('initial_prompt')

            assert llm_client == mock_gemini_client.return_value


def test_get_llm_client_openai():
    with patch('app.nlp.llm_client_factory.os') as mock_os:
        mock_os.environ.get.return_value = 'openai'

        with patch('app.nlp.llm_client_factory.OpenAIClient') as mock_openai_client:
            llm_client = LLMClientFactory.create_llm_client('initial_prompt')

            assert llm_client == mock_openai_client.return_value


def test_get_llm_client_llama():
    with patch('app.nlp.llm_client_factory.os') as mock_os:
        mock_os.environ.get.return_value = 'llama'

        with patch('app.nlp.llm_client_factory.LlamaAIClient') as mock_llama_client:
            llm_client = LLMClientFactory.create_llm_client('initial_prompt')

            assert llm_client == mock_llama_client.return_value


def test_get_llm_client_invalid():
    with patch('app.nlp.llm_client_factory.os') as mock_os:
        mock_os.environ.get.return_value = 'invalid'

        try:
            LLMClientFactory.create_llm_client('initial_prompt')
            assert False
        except ValueError as e:
            assert str(e) == 'Invalid LLM client name: invalid'
