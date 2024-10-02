import json
from datetime import timedelta, datetime
import os
from typing import List
from fastapi import APIRouter
from dateutil.parser import parse
from pydantic import BaseModel, Field
from ml.model import load_model, get_data, resample_data, save_predictions

router = APIRouter(
    prefix="/solar/anomaly_detection",
    tags=["solar", "anomaly_detection"],
    responses={400: {"description": "Could not get anomaly detection"}},
)


class Request(BaseModel):
    cli_id: int
    loc_id: int
    gen_id: int
    start_date: datetime
    end_date: datetime


class Chart(BaseModel):
    from_: str = Field(alias='from')
    to: str
    resultCode: int
    resultText: str


class Prediction(BaseModel):
    dataDate: str
    prediction: float
    actual: float


class Response(BaseModel):
    chart: Chart
    data: List[Prediction]


def parse_request(param_json) -> Request:
    params = json.loads(param_json)
    start_date = params.get('from')
    end_date = params.get('to')
    if start_date:
        start_date = parse(start_date, dayfirst=False, yearfirst=True)
    if end_date:
        end_date = parse(end_date, dayfirst=False,
                         yearfirst=True) + timedelta(days=1, seconds=-1)

    cli_id = params.get('client')
    gen_id = params.get('generator')
    loc_id = params.get('location')

    return Request(start_date=start_date,
                   end_date=end_date,
                   cli_id=cli_id,
                   gen_id=gen_id,
                   loc_id=loc_id)


@router.get("/", tags=["solar", "anomaly_detection"], response_model=Response)
def process_anomaly_detection(param_json):
    request = parse_request(param_json)

    df, loc_capacity, loc_lat, loc_long = get_data(request.cli_id, request.loc_id, request.gen_id, request.start_date, request.end_date)
    if df.empty:
        return Response(chart=Chart(**{"from": request.start_date.strftime("%Y/%m/%d %H:%M:%S"),
                                       "to": request.end_date.strftime("%Y/%m/%d %H:%M:%S"),
                                       "resultCode": 200,
                                       "resultText": "No data found"}), data=[])
    model_df = resample_data(df)
    ml_model = load_model(os.path.join('ml', 'models', 'cat_boost_model.pkl'), loc_capacity)

    input_data = ml_model.generate_input(loc_lat, loc_long, model_df)
    prediction = ml_model.predict(input_data)

    predictions = []
    datas = []

    for i, pred in prediction.iterrows():
        for j in range(4):
            data_date = i - timedelta(minutes=15*j)
            data_pro_id = df.loc[data_date]['data_pro_id']
            actual_power = df.loc[data_date]['Generated Power']
            actual_power = round(actual_power, 3)
            predicted_power = pred['Prediction']

            predictions.append((data_date, predicted_power, data_pro_id))
            data = Prediction(**{"dataDate": data_date.strftime("%Y/%m/%d %H:%M:%S"),
                                 "prediction": predicted_power,
                                 "actual": actual_power})
            datas.append(data)

    save_predictions(request.cli_id, request.gen_id, predictions)

    datas.sort(key=lambda x: x.dataDate)
    chart = Chart(**{"from": request.start_date.strftime("%Y/%m/%d %H:%M:%S"),
                     "to": request.end_date.strftime("%Y/%m/%d %H:%M:%S"),
                     "resultCode": 200,
                     "resultText": ''})

    return Response(chart=chart, data=datas)
