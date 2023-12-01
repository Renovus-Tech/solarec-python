import json
from datetime import timedelta, datetime
from typing import List
from fastapi import APIRouter
from dateutil.parser import parse
from pydantic import BaseModel, Field
from falcon_db.solar import Solar

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


class Response(BaseModel):
    chart: Chart
    data: List[Data]


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
def overview(param_json):
    request = parse_request(param_json)

    solar = Solar(request.client, request.location, None, None, request.start_date, request.end_date, None)
    solar.fetch_aggregated_by_loc_and_period()

    data = solar.data_aggregated_by_loc_and_period.iloc[0]

    chart = Chart(**{"from": data['from'].strftime("%Y/%m/%d %H:%M:%S"),
                     "to": data['to'].strftime("%Y/%m/%d %H:%M:%S"),
                     "resultCode": 200,
                     "resultText": ''})

    data = Data(productionMwh=round(data['ac_production'], 1),
                irradiationKwhM2=round(data['irradiation'], 1),
                avgAmbientTemp=round(data['avg_ambient_temp'], 1),
                avgModuleTemp=round(data['avg_module_temp'], 1),
                specificYield=round(data['loc_specific_yield'], 1),
                performanceRatio=round(data['loc_performance_ratio'], 1),
                timeBasedAvailability=round(data['time_based_availability'] * 100, 1),
                code=solar.gen_codes,
                id=solar.gen_ids,
                name=solar.gen_names)

    return Response(chart=chart, data=[data])
