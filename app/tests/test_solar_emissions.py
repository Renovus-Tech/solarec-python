from datetime import datetime
from unittest import mock

import pandas as pd

from app.endpoints.solar.solar_emissions import parse_request, emissions


def test_parse_request():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1, "location": 1, "groupBy": "hour"}'
    request = parse_request(param_json)

    assert request.start_date == datetime(2021, 1, 1, 0, 0, 0)
    assert request.end_date == datetime(2021, 1, 2, 23, 59, 59)
    assert request.client == 1
    assert request.location == 1
    assert request.freq == "1H"
    assert request.group_by == "hour"


def test_parse_request_no_group_by():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1, "location": 1}'
    request = parse_request(param_json)

    assert request.start_date == datetime(2021, 1, 1, 0, 0, 0)
    assert request.end_date == datetime(2021, 1, 2, 23, 59, 59)
    assert request.client == 1
    assert request.location == 1
    assert request.freq == "100Y"
    assert request.group_by == None


@mock.patch("app.endpoints.solar.solar_emissions.calculate_co2_avoided")
def test_emissions(mock_calculate_co2_avoided):
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1, "location": 1, "groupBy": "hour"}'

    mock_calculate_co2_avoided.return_value = pd.DataFrame({
        "co2_avoided": [10, 20, 30],
        "co2_per_mwh": [0.1, 0.2, 0.3],
        "from": datetime(2021, 1, 1, 0, 0, 0),
        "to": datetime(2021, 1, 2, 0, 0, 0)
    })

    response = emissions(param_json)

    assert response.chart.from_ == "2021/01/01 00:00:00"
    assert response.chart.to == "2021/01/02 23:59:59"
    assert response.chart.resultCode == 200
    assert response.chart.resultText == ""
    assert len(response.data) == 3
    assert response.data[0].from_ == "2021/01/01 00:00:00"
    assert response.data[0].to == "2021/01/02 00:00:00"
    assert response.data[0].co2Avoided == 10
    assert response.data[0].co2PerMwh == 0.1
    assert response.data[1].from_ == "2021/01/01 00:00:00"
    assert response.data[1].to == "2021/01/02 00:00:00"
    assert response.data[1].co2Avoided == 20
    assert response.data[1].co2PerMwh == 0.2
    assert response.data[2].from_ == "2021/01/01 00:00:00"
    assert response.data[2].to == "2021/01/02 00:00:00"
    assert response.data[2].co2Avoided == 30
    assert response.data[2].co2PerMwh == 0.3
