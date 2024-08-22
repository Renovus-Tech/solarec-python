import json
from db.utils import get_location, update_location
from nlp.llm_client_factory import LLMClientFactory
from fastapi import APIRouter, HTTPException, status
from nlp.onboarding_helper import NLPOnboardingHelper
from pydantic import BaseModel
from db.db import session

router = APIRouter(
    prefix="/solar/location/onboard",
    tags=["solar", "location", "onboard"]
)


class Request(BaseModel):
    client_id: int
    location_id: int
    text: str


class Response(BaseModel):
    client_id: int
    location_id: int
    address: str
    capacity: int
    installation_date: str


def parse_request(param_json) -> Request:
    params = json.loads(param_json)
    client = params['client']
    location = params['location']
    text = params['text']

    return Request(client_id=client,
                   location_id=location,
                   text=text)


@router.post("/", status_code=status.HTTP_200_OK, response_model=Response)
def onboard_location(param_json):
    request = parse_request(param_json)
    location = get_location(session, request.location_id, request.client_id)
    if not location:
        raise HTTPException(
            status_code=404, detail=f"No Location was found for the location ID: {request.location_id} and client ID: {request.client_id}")

    llm_client = LLMClientFactory.create_llm_client()
    onboarding_helper = NLPOnboardingHelper(llm_client)
    response = onboarding_helper.get_onboarding_data(request.text)

    if not response:
        raise HTTPException(
            status_code=404, detail="No data was found for the given text")

    update_location(location, response.address, response.capacity)

    return Response(location_id=request.location_id,
                    client_id=request.client_id,
                    address=response.address,
                    capacity=response.capacity,
                    installation_date=response.installation_date)
