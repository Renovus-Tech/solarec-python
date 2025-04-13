import json
from datetime import datetime, timedelta
from typing import List, Optional

from core.solar_expected_power import get_expected_power
from dateutil.parser import parse
from db.db import get_db
from db.utils import data_freq_to_pd_frequency, group_by_to_pd_frequency
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/solar/expected_power",
    tags=["solar", "expected_power"],
    responses={400: {"description": "Could not get expected_power"}},
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
    expectedProductionMwh: float


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
    data_freq: Optional[str] = '15T'


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
    data_freq = data_freq_to_pd_frequency(params['frqNumber'], params['frqUnit'])

    return Request(start_date=start_date,
                   end_date=end_date,
                   client=client,
                   location=location,
                   freq=freq,
                   group_by=group_by,
                   data_freq=data_freq)


@router.get("/", tags=["solar", "expected_power"], response_model=Response)
def expected_power(param_json, db: Session = Depends(get_db)):
    request = parse_request(param_json)
    data = get_expected_power(db, request.client, request.location, request.start_date, request.end_date, request.freq, request.data_freq)

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
                             "expectedProductionMwh": round(row['expected_power'], 3)
                             }))

    return Response(chart=chart, data=datas)
