from typing import Optional
from pydantic import BaseModel

from nlp.llm_client import LLMClient


class OnboardingData(BaseModel):
    ''' Data class for onboarding data'''
    address: Optional[str]
    capacity: Optional[int]
    installation_date: Optional[str]


class NLPOnboardingHelper():
    ''' Helper class for generating onboarding data from an LLMClient'''

    def __init__(self, llm_client: LLMClient):
        self.client = llm_client

    def get_onboarding_data(self, user_input):
        ''' Generate onboarding data based on the user input'''

        data = self.client.generate_json(user_input)
        if not data:
            return None
        return OnboardingData(address=data.get('address', None),
                              capacity=data.get('capacity', None),
                              installation_date=data.get('installation_date', None))
