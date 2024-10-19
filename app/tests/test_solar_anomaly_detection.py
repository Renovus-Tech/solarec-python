from datetime import datetime
from typing import Tuple
from unittest import mock

import pandas as pd
import pytest

from app.endpoints.solar.solar_anomaly_detection import parse_request, process_anomaly_detection


def test_parse_request():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1, "location": 1, "generator": 1, "data_pro_id": 1}'
    request = parse_request(param_json)

    assert request.start_date == datetime(2021, 1, 1, 0, 0, 0)
    assert request.end_date == datetime(2021, 1, 2, 23, 59, 59)
    assert request.cli_id == 1
    assert request.loc_id == 1
    assert request.gen_id == 1
    assert request.data_pro_id == 1


def test_parse_request():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1, "location": 1, "generator": 1, "data_pro_id": 1}'
    request = parse_request(param_json)

    assert request.start_date == datetime(2021, 1, 1, 0, 0, 0)
    assert request.end_date == datetime(2021, 1, 2, 23, 59, 59)
    assert request.cli_id == 1
    assert request.loc_id == 1
    assert request.gen_id == 1
    assert request.data_pro_id == 1


def test_parse_request_with_data_pro_id():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "data_pro_id": 1}'
    request = parse_request(param_json)

    assert request.start_date == datetime(2021, 1, 1, 0, 0, 0)
    assert request.end_date == datetime(2021, 1, 2, 23, 59, 59)
    assert request.cli_id is None
    assert request.loc_id is None
    assert request.gen_id is None
    assert request.data_pro_id == 1


def test_parse_request_should_fail():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1}'
    with pytest.raises(ValueError) as exception:
        parse_request(param_json)
    assert exception.value.args[0] == "Invalid parameters: either data_pro_id or client, location, generator, start and end dates must be provided"


@mock.patch("app.endpoints.solar.solar_anomaly_detection.get_data")
@mock.patch("app.endpoints.solar.solar_anomaly_detection.resample_data")
@mock.patch("app.endpoints.solar.solar_anomaly_detection.load_model")
@mock.patch("app.endpoints.solar.solar_anomaly_detection.save_predictions")
def test_process_anomaly_detection(mock_save_predictions, mock_load_model, mock_resample_data, mock_get_data):
    param_json = '{"from": "2021/01/01T00:00:00", "to": "2021/01/02T00:00:00", "client": 1, "location": 1, "generator": 1}'
    df = pd.DataFrame({
        "data_pro_id": [1, 1, 1, 1, 1],
        "Generated Power": [10, 20, 30, 40, 50],
    }, index=[datetime(2021, 1, 1, 0, 0, 0), datetime(2021, 1, 1, 0, 15, 0), datetime(2021, 1, 1, 0, 30, 0), datetime(2021, 1, 1, 0, 45, 0), datetime(2021, 1, 1, 1, 0, 0)])
    mock_get_data.return_value = (df, 1,
                                  1,
                                  1,
                                  datetime(2021, 1, 1, 0, 0, 0),
                                  datetime(2021, 1, 2, 23, 59, 59),
                                  100,
                                  1.0,
                                  1.0)

    mock_resample_data.return_value = df

    mock_model = mock_load_model.return_value
    df_predict = df = pd.DataFrame({
        "Prediction": [30],
    }, index=[datetime(2021, 1, 1, 1, 0, 0)])
    mock_model.predict.return_value = df_predict
    mock_model.generate_input.return_value = df

    response = process_anomaly_detection(param_json)

    assert response.chart.from_ == "2021/01/01 00:00:00"
    assert response.chart.to == "2021/01/02 23:59:59"
    assert response.chart.resultCode == 200
    assert response.chart.resultText == ""
    assert len(response.data) == 4
    assert response.data[0].actual == 20
    assert response.data[0].prediction == 30
    assert response.data[0].dataDate == '2021/01/01 00:15:00'
    assert response.data[1].actual == 30
    assert response.data[1].prediction == 30
    assert response.data[1].dataDate == '2021/01/01 00:30:00'
    assert response.data[2].actual == 40
    assert response.data[2].prediction == 30
    assert response.data[2].dataDate == '2021/01/01 00:45:00'
    assert response.data[3].actual == 50
    assert response.data[3].prediction == 30
    assert response.data[3].dataDate == '2021/01/01 01:00:00'
