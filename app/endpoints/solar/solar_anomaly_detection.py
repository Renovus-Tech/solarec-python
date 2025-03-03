import json
from datetime import timedelta, datetime
import os
from typing import List, Optional
from fastapi import APIRouter, Depends
from dateutil.parser import parse
from pydantic import BaseModel, Field
from db.db import get_db
from ml.model import load_model, get_data, resample_data, save_predictions
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/solar/anomaly_detection",
    tags=["solar", "anomaly_detection"],
    responses={400: {"description": "Could not get anomaly detection"}},
)


class Request(BaseModel):
    cli_id: Optional[int]
    loc_id: Optional[int]
    gen_id: Optional[int]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    data_pro_id: Optional[int]


class Chart(BaseModel):
    from_: Optional[str] = Field(alias='from')
    to: Optional[str]
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
    data_pro_id = params.get('data_pro_id')

    if not data_pro_id and not (cli_id and loc_id and gen_id and start_date and end_date):
        raise ValueError('Invalid parameters: either data_pro_id or client, location, generator, start and end dates must be provided')

    return Request(start_date=start_date,
                   end_date=end_date,
                   cli_id=cli_id,
                   gen_id=gen_id,
                   loc_id=loc_id,
                   data_pro_id=data_pro_id)


@router.get("/", tags=["solar", "anomaly_detection"], response_model=Response)
def process_anomaly_detection(param_json, db: Session = Depends(get_db)):
    request = parse_request(param_json)

    df, cli_id, loc_id, gen_id, start_date, end_date, loc_capacity, loc_lat, loc_long = get_data(db,
                                                                                                 start_date=request.start_date,
                                                                                                 end_date=request.end_date,
                                                                                                 cli_id=request.cli_id,
                                                                                                 loc_id=request.loc_id,
                                                                                                 gen_id=request.gen_id,
                                                                                                 data_pro_id=request.data_pro_id)
    if df.empty:
        return Response(chart=Chart(**{"resultCode": 200,
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

    save_predictions(db, cli_id, gen_id, predictions)

    datas.sort(key=lambda x: x.dataDate)
    chart = Chart(**{"from": start_date.strftime("%Y/%m/%d %H:%M:%S"),
                     "to": end_date.strftime("%Y/%m/%d %H:%M:%S"),
                     "resultCode": 200,
                     "resultText": ''})

    return Response(chart=chart, data=datas)
