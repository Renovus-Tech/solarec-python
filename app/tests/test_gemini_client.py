from unittest.mock import patch

from app.nlp.gemini_client import GeminiAIClient


def test_construct_gemini_client():

    with patch('app.nlp.gemini_client.os.environ.get') as mock_get_env:
        mock_get_env.side_effect = lambda key: {
            "GEMINI_API_KEY": "fake_api_key",
            "GEMINI_MODEL_NAME": "test_model",
            "GEMINI_INITIAL_PROMPT": "test_prompt"
        }.get(key)

        with patch('app.nlp.gemini_client.genai') as mock_genai:
            mock_genai.configure = patch('app.nlp.gemini_client.genai.configure').start()
            mock_genai.GenerativeModel = patch('app.nlp.gemini_client.genai.GenerativeModel').start()

            gemini_client = GeminiAIClient()

            assert gemini_client is not None
            mock_genai.configure.assert_called_once_with(api_key='fake_api_key')
            mock_genai.GenerativeModel.assert_called_once_with('test_model', system_instruction='test_prompt')


def test_generate_text():
    with patch('app.nlp.gemini_client.os.environ.get') as mock_get_env:
        mock_get_env.side_effect = lambda key: {
            "GEMINI_API_KEY": "fake_api_key",
            "GEMINI_MODEL_NAME": "test_model",
            "GEMINI_INITIAL_PROMPT": "test_prompt"
        }.get(key)

        with patch('app.nlp.gemini_client.genai.GenerativeModel') as mock_GenerativeModel:
            mock_model_instance = mock_GenerativeModel.return_value
            mock_model_instance.generate_content.return_value = 'Generated text'

            gemini_client = GeminiAIClient()
            generated_text = gemini_client.generate_text('prompt')

            assert generated_text == 'Generated text'
