from pydantic import BaseModel
from app.nlp.llm_client import LLMClient

class OnboardingData(BaseModel):
    ''' Data class for onboarding data'''
    location: str
    capacity: int
    installation_date: str    


class NLPOnboardingHelper():
    ''' Helper class for generating onboarding data from an LLMClient'''

    def __init__(self, llm_client: LLMClient):
        self.client = llm_client

    def get_onboarding_data(self, user_input):
        ''' Generate onboarding data based on the user input'''

        data = self.client.generate_json(user_input)
        return OnboardingData(location=data['location'],
                              capacity=data['capacity'],
                              installation_date=data['installation_date'])
