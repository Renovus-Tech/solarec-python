from unittest.mock import MagicMock, patch

from app.nlp.openai_client import OpenAIClient


def test_construct_openai_client():
    with patch('app.nlp.openai_client.os.environ.get') as mock_get_env:
        mock_get_env.side_effect = lambda key: {
            "OPENAI_API_KEY": "fake_api_key",
            "OPENAI_MODEL_NAME": "text-davinci-003",
            "OPENAI_INITIAL_PROMPT": "test_prompt"
        }.get(key)

        with patch('app.nlp.openai_client.openai.ChatCompletion.create') as mock_create:
            mock_create.return_value = MagicMock()

            openai_client = OpenAIClient()

            assert openai_client is not None
            mock_create.assert_called_once_with(
                engine='text-davinci-003',
                prompt='test_prompt',
                max_tokens=100,
                api_key='fake_api_key'
            )


def test_generate_text():
    with patch('app.nlp.openai_client.os.environ.get') as mock_get_env:
        mock_get_env.side_effect = lambda key: {
            "OPENAI_API_KEY": "fake_api_key",
            "OPENAI_MODEL_NAME": "text-davinci-003",
            "OPENAI_INITIAL_PROMPT": "test_prompt"
        }.get(key)

        with patch('app.nlp.openai_client.openai.ChatCompletion.create') as mock_create:
            mock_client_instance = MagicMock()
            mock_client_instance.generate.return_value = MagicMock(choices=[MagicMock(message={'content': 'Generated text'})])
            mock_create.return_value = mock_client_instance

            openai_client = OpenAIClient()
            generated_text = openai_client.generate_text('prompt')

            assert generated_text == 'Generated text'
