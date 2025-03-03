import json
from datetime import timedelta, datetime
from typing import List, Optional
from db.db import get_db
from db.utils import data_freq_to_pd_frequency, group_by_to_pd_frequency, pandas_frequency_to_timedelta
from fastapi import APIRouter, Depends, HTTPException
from dateutil.parser import parse
from pydantic import BaseModel, Field
from core.solar import Solar
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/solar/performance",
    tags=["solar", "performance"],
    responses={400: {"description": "Could not get performance"}},
)


class Chart(BaseModel):
    from_: str = Field(alias='from')
    to: str
    resultCode: int
    resultText: str
    groupBy: Optional[str]


class GenData(BaseModel):
    id: int
    name: str
    code: str
    productionMwh: float
    acProductionMwh: float
    irradiationKwhM2: float
    performanceRatio: float
    timeBasedAvailability: float


class Data(BaseModel):
    from_: str = Field(alias='from')
    to: str
    genData: List[GenData]
    totalProductionMwh: float
    totalACProductionMwh: float
    totalIrradiationKwhM2: float
    performanceRatio: float
    timeBasedAvailability: float


class Response(BaseModel):
    chart: Chart
    data: List[Data]


class Request(BaseModel):
    start_date: datetime
    end_date: datetime
    client: int
    location: int
    generators: List[int]
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
    generators = params['generators']
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
                   generators=generators,
                   freq=freq,
                   data_freq=data_freq,
                   group_by=group_by)


@router.get("/", tags=["solar", "performance"], response_model=Response)
def performance(param_json, db: Session = Depends(get_db)):
    request = parse_request(param_json)

    if request.freq is not None:
        data_freq_timedelta = pandas_frequency_to_timedelta(request.data_freq)
        freq_timedelta = pandas_frequency_to_timedelta(request.freq)
        if freq_timedelta < data_freq_timedelta:
            raise HTTPException(status_code=400, detail=f'Invalid group_by {request.group_by} for frequence {request.data_freq}')

    solar = Solar(db, request.client, request.location, request.generators, None, request.start_date, request.end_date, request.freq, request.data_freq)

    solar.fetch_aggregated_by_loc_and_period(db)

    chart = Chart(**{"from": request.start_date.strftime("%Y/%m/%d %H:%M:%S"),
                     "to": request.end_date.strftime("%Y/%m/%d %H:%M:%S"),
                     "resultCode": 200,
                     "resultText": '',
                     "groupBy": request.group_by})

    datas = []
    for date, row in solar.data_aggregated_by_loc_and_period.iterrows():
        gen_datas = []
        for gen_id in request.generators:
            gen_row = solar.data_aggregated_by_period.loc[gen_id, date]
            gen_code_and_name = solar.gen_codes_and_names.loc[gen_id]
            gen_code = gen_code_and_name['gen_code']
            gen_name = gen_code_and_name['gen_name']
            gen_data = GenData(id=gen_id,
                               name=gen_name,
                               code=gen_code,
                               productionMwh=round(gen_row['power'], 3),
                               acProductionMwh=round(gen_row['ac_production'], 3),
                               irradiationKwhM2=round(gen_row['irradiation'], 1),
                               performanceRatio=round(gen_row['performance_ratio'], 1),
                               timeBasedAvailability=round(gen_row['time_based_availability'], 1))
            gen_datas.append(gen_data)

        data = Data(**{"from": row['from'].strftime("%Y/%m/%d %H:%M:%S"),
                       "to": row['to'].strftime("%Y/%m/%d %H:%M:%S"),
                       "totalProductionMwh": round(row['power'], 3),
                       "totalACProductionMwh": round(row['ac_production'], 3),
                       "totalIrradiationKwhM2": round(row['irradiation'], 1),
                       "performanceRatio": round(row['performance_ratio'], 1),
                       "timeBasedAvailability": round(row['time_based_availability'], 1),
                       "genData": gen_datas})
        datas.append(data)

    return Response(chart=chart, data=datas)
