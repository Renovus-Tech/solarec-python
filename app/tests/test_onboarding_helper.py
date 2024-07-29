from unittest.mock import patch

from app.nlp.llm_client_factory import LLMClientFactory
from app.nlp.onboarding_helper import NLPOnboardingHelper


def test_get_onboarding_data():

    with patch('app.nlp.onboarding_helper.LLMClient') as mock_llm_client:
        mock_llm_client.generate_json.return_value = {
            'location': 'New York',
            'capacity': 1000,
            'installation_date': '2022-01-01'
        }
        onboarding_helper = NLPOnboardingHelper(mock_llm_client)

        onboarding_data = onboarding_helper.get_onboarding_data('The location is New York, the capacity is 1000, and the installation date is 2022-01-01')

        assert onboarding_data.location == 'New York'
        assert onboarding_data.capacity == 1000
        assert onboarding_data.installation_date == '2022-01-01'


def test_get_onboarding_data_empty():
    with patch('app.nlp.onboarding_helper.LLMClient') as mock_llm_client:
        mock_llm_client.generate_json.return_value = {}
        onboarding_helper = NLPOnboardingHelper(mock_llm_client)

        onboarding_data = onboarding_helper.get_onboarding_data('A random text with no information')

        assert onboarding_data is None
