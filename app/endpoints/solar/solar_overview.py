import json
from datetime import datetime, timedelta
from typing import List, Optional

from core.solar import Solar
from dateutil.parser import parse
from db.db import get_db
from db.utils import data_freq_to_pd_frequency
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/solar/overview",
    tags=["solar", "overview"],
    responses={400: {"description": "Could not get overview"}},
)


class Chart(BaseModel):
    from_: str = Field(alias='from')
    to: str
    resultCode: int
    resultText: str


class Data(BaseModel):
    id: List[int]
    name: List[str]
    code: List[str]
    productionMwh: float
    irradiationKwhM2: float
    avgAmbientTemp: float
    avgModuleTemp: float
    timeBasedAvailability: float
    specificYield: float
    performanceRatio: float
    certificates: float
    capacityFactor: float


class Response(BaseModel):
    chart: Chart
    data: List[Data]


class Request(BaseModel):
    start_date: datetime
    end_date: datetime
    client: int
    location: int
    data_freq: Optional[str] = '15T'


def parse_request(param_json) -> Request:
    params = json.loads(param_json)
    start_date = parse(params['from'], dayfirst=False, yearfirst=True)
    end_date = parse(params['to'], dayfirst=False,
                     yearfirst=True) + timedelta(days=1, seconds=-1)
    client = params['client']
    location = params['location']
    params['frqNumber'] = params.get('frqNumber', 15)
    params['frqUnit'] = params.get('frqUnit', 'm')
    data_freq = data_freq_to_pd_frequency(params['frqNumber'], params['frqUnit'])

    return Request(start_date=start_date,
                   end_date=end_date,
                   client=client,
                   location=location,
                   data_freq=data_freq)


@router.get("/", tags=["solar", "overview"], response_model=Response)
def overview(param_json, db: Session = Depends(get_db)):
    request = parse_request(param_json)
    solar = Solar(db, request.client, request.location, None, None, request.start_date, request.end_date, None, request.data_freq)
    solar.fetch_aggregated_by_loc_and_period(db)

    if solar.data is None:

        chart = Chart(**{"from": request.start_date.strftime("%Y/%m/%d %H:%M:%S"),
                         "to": request.end_date.strftime("%Y/%m/%d %H:%M:%S"),
                         "resultCode": 200,
                         "resultText": ''})
        return Response(chart=chart, data=[])

    data = solar.data_aggregated_by_loc_and_period.iloc[0]

    chart = Chart(**{"from": data['from'].strftime("%Y/%m/%d %H:%M:%S"),
                     "to": data['to'].strftime("%Y/%m/%d %H:%M:%S"),
                     "resultCode": 200,
                     "resultText": ''})
    ac_production = round(data['ac_production'], 3)
    data = Data(productionMwh=ac_production,
                irradiationKwhM2=round(data['irradiation'], 1),
                avgAmbientTemp=round(data['avg_ambient_temp'], 1),
                avgModuleTemp=round(data['avg_module_temp'], 1),
                specificYield=round(data['loc_specific_yield'], 1),
                performanceRatio=round(data['loc_performance_ratio'], 1),
                timeBasedAvailability=round(data['time_based_availability'] * 100, 1),
                code=solar.gen_codes,
                id=solar.gen_ids,
                name=solar.gen_names,
                certificates=ac_production,
                capacityFactor=round(data['capacity_factor'] * 100, 1))

    return Response(chart=chart, data=[data])
