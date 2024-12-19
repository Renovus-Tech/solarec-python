import json
from datetime import datetime, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd
from db.utils import data_freq_to_pd_frequency, get_period_end
from core.solar import Solar
from dateutil.parser import parse
from fastapi import APIRouter
from pydantic import BaseModel, Field

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
    data_freq: Optional[str] = '15T'


def parse_request(param_json) -> Request:
    params = json.loads(param_json)
    start_date = parse(params['from'], dayfirst=False, yearfirst=True)
    end_date = parse(params['to'], dayfirst=False,
                     yearfirst=True) + timedelta(days=1, seconds=-1)
    client = params['client']
    location = params['location']
    generators = params['generators']
    params['frqNumber'] = params.get('frqNumber', 15)
    params['frqUnit'] = params.get('frqUnit', 'm')
    data_freq = data_freq_to_pd_frequency(params['frqNumber'], params['frqUnit'])

    return Request(start_date=start_date,
                   end_date=end_date,
                   client=client,
                   location=location,
                   generators=generators,
                   data_freq=data_freq)


def _adjust_units(row, data_freq, datetime_end):
    row_start_date = row.name[1]
    row_end_date = get_period_end(row_start_date, data_freq, datetime_end)
    seconds_in_one_hour = 60*60
    seconds_in_row_period = (row_end_date - row_start_date).total_seconds() + 1
    multiplier = seconds_in_one_hour / seconds_in_row_period
    row_value = row[0]
    if row_value is not None:
        return row_value * multiplier


@router.get("/", tags=["solar", "power_curve"], response_model=Response)
def power_curve(param_json):
    request = parse_request(param_json)
    solar = Solar(request.client, request.location, request.generators, None, request.start_date, request.end_date, "100Y", request.data_freq)

    solar.fetch_data()
    power_curve = solar.data[['ac_production', 'irradiation']]

    power_curve["ac_production"] = power_curve[["ac_production"]].apply(lambda x: _adjust_units(x, request.data_freq, request.end_date), axis=1)
    power_curve["irradiation"] = power_curve[["irradiation"]].apply(lambda x: _adjust_units(x, request.data_freq, request.end_date), axis=1)
    power_curve.fillna(0, inplace=True)
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
