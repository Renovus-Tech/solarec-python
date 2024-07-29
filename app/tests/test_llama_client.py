from unittest.mock import MagicMock, patch

from app.nlp.llama_client import LlamaAIClient


def test_construct_llama_client():
    with patch('app.nlp.llama_client.os.environ.get') as mock_get_env:
        mock_get_env.side_effect = lambda key: {
            "LLAMA_API_KEY": "fake_api_key",
            "LLAMA_BASE_URL": "https://api.example.com",
            "LLAMA_MODEL_NAME": "text-davinci-003",
            "LLAMA_INITIAL_PROMPT": "test_prompt"
        }.get(key)

        with patch('app.nlp.llama_client.OpenAI') as mock_openai:
            mock_openai.return_value = MagicMock()

            llama_client = LlamaAIClient()

            assert llama_client is not None
            mock_openai.assert_called_once_with(
                api_key='fake_api_key',
                base_url='https://api.example.com'
            )


def test_generate_text():
    with patch('app.nlp.llama_client.os.environ.get') as mock_get_env:
        mock_get_env.side_effect = lambda key: {
            "LLAMA_API_KEY": "fake_api_key",
            "LLAMA_BASE_URL": "https://api.example.com",
            "LLAMA_MODEL_NAME": "text-davinci-003",
            "LLAMA_INITIAL_PROMPT": "test_prompt"
        }.get(key)

        with patch('app.nlp.llama_client.OpenAI') as mock_openai:
            mock_client_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.model_dump_json.return_value = MagicMock(choices=[MagicMock(message={'content': 'Generated text'})])
            mock_client_instance.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client_instance

            llama_client = LlamaAIClient()
            generated_text = llama_client.generate_text('prompt')

            assert generated_text == 'Generated text'
