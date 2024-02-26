import json
from datetime import timedelta, datetime
from typing import List, Optional
from fastapi import APIRouter
from dateutil.parser import parse
from pydantic import BaseModel, Field
from core import solar_alerts

router = APIRouter(
    prefix="/solar/alerts",
    tags=["solar", "alerts"],
    responses={400: {"description": "Could not get alerts"}},
)


class Data(BaseModel):
    from_: str = Field(alias='from')
    to: str
    count: int
    client: int
    location: int
    generators: List[int]


class Response(BaseModel):
    data: Data


class Request(BaseModel):
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    client: Optional[int]
    location: Optional[int]
    data_pro_id: Optional[int]


def parse_request(param_json) -> Request:
    params = json.loads(param_json)
    start_date = params.get('from')
    end_date = params.get('to')
    if start_date:
            start_date = parse(start_date, dayfirst=False, yearfirst=True)
    if end_date:         
        end_date = parse(end_date, dayfirst=False,
                     yearfirst=True) + timedelta(days=1, seconds=-1)

    data_pro_id = params.get('data_pro_id')
    client = params.get('client')
    location = params.get('location')

    if not data_pro_id and not (client and location and start_date and end_date):
        raise ValueError('Invalid parameters: either data_pro_id or client and location must be provided')
    return Request(start_date=start_date,
                    end_date=end_date,
                    client=client,
                    location=location,
                    data_pro_id=data_pro_id)

    


@router.get("/", tags=["solar", "overview"], response_model=Response)
def process_alerts(param_json):
    request = parse_request(param_json)
    cli_id, loc_id, gen_ids, datetime_start, datetime_end, alert_count = solar_alerts.calculate_alerts(cli_id=request.client, loc_id=request.location, data_pro_id=request.data_pro_id, datetime_start=request.start_date, datetime_end=request.end_date)
    return Response(data=Data(**{"from": datetime_start.strftime('%Y-%m-%d %H:%M'), "to": datetime_end.strftime('%Y-%m-%d %H:%M'), "count": alert_count, "client": cli_id, "location": loc_id, "generators": gen_ids}))

