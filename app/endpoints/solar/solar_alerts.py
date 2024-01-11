import json
from datetime import timedelta, datetime
from fastapi import APIRouter
from dateutil.parser import parse
from pydantic import BaseModel
from core import solar_alerts

router = APIRouter(
    prefix="/solar/alerts",
    tags=["solar", "alerts"],
    responses={400: {"description": "Could not get alerts"}},
)


class Data(BaseModel):
    from_: str
    to: str
    count: int


class Response(BaseModel):
    data: Data


class Request(BaseModel):
    start_date: datetime
    end_date: datetime
    client: int
    location: int


def parse_request(param_json) -> Request:
    params = json.loads(param_json)
    start_date = parse(params['from'], dayfirst=False, yearfirst=True)
    end_date = parse(params['to'], dayfirst=False,
                     yearfirst=True) + timedelta(days=1, seconds=-1)
    client = params['client']
    location = params['location']

    return Request(start_date=start_date,
                   end_date=end_date,
                   client=client,
                   location=location)


@router.get("/", tags=["solar", "overview"], response_model=Response)
def process_alerts(param_json):
    request = parse_request(param_json)

    alert_count = solar_alerts.calculate_alerts(cli_id=request.client, loc_id=request.location, datetime_start=request.start_date, datetime_end=request.end_date)
    return Response(data=Data(from_=request.start_date.strftime('%Y-%m-%d'), to=request.end_date.strftime('%Y-%m-%d'), count=alert_count))

