import json
from datetime import timedelta, datetime
from typing import List, Optional
from core.solar_emissions import calculate_co2_avoided
from db.utils import data_freq_to_pd_frequency, group_by_to_pd_frequency, pandas_frequency_to_timedelta
from fastapi import APIRouter, HTTPException
from dateutil.parser import parse
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/solar/emissions",
    tags=["solar", "emissions"],
    responses={400: {"description": "Could not get emissions"}},
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
    co2Avoided: float
    co2PerMwh: float


class Response(BaseModel):
    chart: Chart
    data: List[Data]


class Request(BaseModel):
    start_date: datetime
    end_date: datetime
    client: int
    location: int
    freq: Optional[str]
    data_freq: Optional[str] = '15T'
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
    data_freq = data_freq_to_pd_frequency(params['frqNumber'], params['frqUnit'])

    return Request(start_date=start_date,
                   end_date=end_date,
                   client=client,
                   location=location,
                   freq=freq,
                   data_freq=data_freq,
                   group_by=group_by)


@router.get("/", tags=["solar", "emissions"], response_model=Response)
def emissions(param_json):
    request = parse_request(param_json)

    if request.freq is not None:
        data_freq_timedelta = pandas_frequency_to_timedelta(request.data_freq)
        freq_timedelta = pandas_frequency_to_timedelta(request.freq)
        if freq_timedelta < data_freq_timedelta:
            raise HTTPException(status_code=400, detail=f'Invalid group_by {request.group_by} for frequence {request.data_freq}')

    data = calculate_co2_avoided(request.client, request.location, request.start_date, request.end_date, request.freq, request.data_freq)
    chart = Chart(**{"from": request.start_date.strftime("%Y/%m/%d %H:%M:%S"),
                     "to": request.end_date.strftime("%Y/%m/%d %H:%M:%S"),
                     "resultCode": 200,
                     "resultText": '',
                     "groupBy": request.group_by})
    datas = []
    for _, row in data.iterrows():
        datas.append(Data(**{"from": row['from'].strftime("%Y/%m/%d %H:%M:%S"),
                             "to": row['to'].strftime("%Y/%m/%d %H:%M:%S"),
                             "co2Avoided": round(row['co2_avoided'], 5),
                             "co2PerMwh": round(row['co2_per_mwh'], 5), }))

    return Response(chart=chart, data=datas)
