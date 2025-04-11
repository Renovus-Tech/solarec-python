import json
from datetime import timedelta, datetime
from typing import List, Optional
from core.solar_data_availability import calculate_data_availability
from db.db import get_db
from db.utils import group_by_to_pd_frequency
from fastapi import APIRouter, Depends
from dateutil.parser import parse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/data_availability",
    tags=["data_availability"],
    responses={400: {"description": "Could not get data availability"}},
)


class Chart(BaseModel):
    from_: str = Field(alias='from')
    to: str
    resultCode: int
    resultText: str
    groupBy: Optional[str]


class Data(BaseModel):
    from_: str = Field(alias='from')
    to: str
    production_data_available_rate: float
    irradiation_data_available_rate: float
    temperature_data_available_rate: float


class Response(BaseModel):
    chart: Chart
    data: List[Data]


class Request(BaseModel):
    start_date: datetime
    end_date: datetime
    client: int
    location: int
    freq: Optional[str]
    group_by: Optional[str]


def parse_request(param_json) -> Request:
    params = json.loads(param_json)
    start_date = parse(params['from'], dayfirst=False, yearfirst=True)
    end_date = parse(params['to'], dayfirst=False,
                     yearfirst=True) + timedelta(days=1, seconds=-1)
    client = params['client']
    location = params['location']
    group_by = params.get('groupBy')
    freq = None
    if group_by:
        freq = group_by_to_pd_frequency(group_by)

    params['frqNumber'] = params.get('frqNumber', 15)
    params['frqUnit'] = params.get('frqUnit', 'm')

    return Request(start_date=start_date,
                   end_date=end_date,
                   client=client,
                   location=location,
                   freq=freq,
                   group_by=group_by)


@router.get("/", tags=["solar", "data_availability"], response_model=Response)
def get_data_availability(param_json, db: Session = Depends(get_db)):

    request = parse_request(param_json)

    data = calculate_data_availability(db, request.client, request.location, request.start_date, request.end_date, request.freq)

    chart = Chart(**{"from": request.start_date.strftime("%Y/%m/%d %H:%M:%S"),
                     "to": request.end_date.strftime("%Y/%m/%d %H:%M:%S"),
                     "resultCode": 200,
                     "resultText": '',
                     "groupBy": request.group_by})
    datas = []

    if data is None:
        return Response(chart=chart, data=datas)

    for _, row in data.iterrows():
        datas.append(Data(**{"from": row['from'].strftime("%Y/%m/%d %H:%M:%S"),
                             "to": row['to'].strftime("%Y/%m/%d %H:%M:%S"),
                             "production_data_available_rate": round(row['production_data_available_rate'], 2),
                             "irradiation_data_available_rate": round(row['irradiation_data_available_rate'], 2),
                             "temperature_data_available_rate": round(row['temperature_data_available_rate'], 2), }))

    return Response(chart=chart, data=datas)
