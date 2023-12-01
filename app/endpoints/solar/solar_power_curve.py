import json
from datetime import timedelta, datetime
from typing import List, Optional
from fastapi import APIRouter
from dateutil.parser import parse
from pydantic import BaseModel, Field
from core.solar import Solar
import pandas as pd
import numpy as np

router = APIRouter(
    prefix="/solar/power_curve",
    tags=["solar", "power_curve"],
    responses={400: {"description": "Could not get power curve"}},
)


class Chart(BaseModel):
    from_: str = Field(alias='from')
    to: str
    resultCode: int
    resultText: str


class Curves(BaseModel):
    power: List[float]
    irradiation: List[float]
    timestamps: List[str]


class Medians(BaseModel):
    power: List[float]
    irradiation: List[float]


class Data(BaseModel):
    curves: Curves
    medians: Medians


class GenData(BaseModel):
    id: int
    name: str
    code: str
    data: Data


class Response(BaseModel):
    chart: Chart
    generator: List[GenData]


class Request(BaseModel):
    start_date: datetime
    end_date: datetime
    client: int
    location: int
    generators: List[int]


def parse_request(param_json) -> Request:
    params = json.loads(param_json)
    start_date = parse(params['from'], dayfirst=False, yearfirst=True)
    end_date = parse(params['to'], dayfirst=False,
                     yearfirst=True) + timedelta(days=1, seconds=-1)
    client = params['client']
    location = params['location']
    generators = params['generators']

    return Request(start_date=start_date,
                   end_date=end_date,
                   client=client,
                   location=location,
                   generators=generators)


@router.get("/", tags=["solar", "performance"], response_model=Response)
def performance(param_json):
    request = parse_request(param_json)

    solar = Solar(request.client, request.location, request.generators, None, request.start_date, request.end_date, "100Y")

    solar.fetch_data()
    power_curve = solar.data[['ac_production', 'irradiation']]
    power_curve["ac_production"] = power_curve["ac_production"].apply(lambda x: x * 4)
    power_curve["irradiation"] = power_curve["irradiation"].apply(lambda x: x * 4)

    gen_data: List[GenData] = []
    for i, gen_id in enumerate(request.generators):
        power_curve_gen = power_curve.loc[gen_id]
        power_curve_gen.sort_values(by=['irradiation'], inplace=True, ascending=True)

        power_curve_grouped_by_irradiation_bins = power_curve_gen.groupby(pd.cut(power_curve_gen['irradiation'], np.arange(0, 1.4, 0.1))).median()
        power_curve_grouped_by_irradiation_bins.dropna(inplace=True)
        medians_irradiation = list([round(x.left, 2) for x in power_curve_grouped_by_irradiation_bins.index.values])
        medians_power = list([round(x, 2) for x in power_curve_grouped_by_irradiation_bins['ac_production'].values])

        # filter by irradiation higer than 0 or power higher than 0.01
        power_curve_gen = power_curve_gen[(power_curve_gen['irradiation'] > 0.01) | (power_curve_gen['ac_production'] > 0.01)]
        power = list([round(x, 2) for x in power_curve_gen['ac_production'].values])
        irradiation = list([round(x, 2) for x in power_curve_gen['irradiation'].values])
        timestamps = list([str(x) for x in power_curve_gen.index])

        curves = Curves(**{"power": power, "irradiation": irradiation, "timestamps": timestamps})
        medians = Medians(**{"power": medians_power, "irradiation": medians_irradiation})
        data = Data(**{"curves": curves, "medians": medians})
        gen_data.append(GenData(**{"id": gen_id, "name": solar.gen_names[i], "code": solar.gen_codes[i], "data": data}))
    return Response(chart=Chart(**{"from": str(request.start_date),
                                   "to": str(request.end_date),
                                   "resultCode": 200,
                                   "resultText": ''}), generator=gen_data)
