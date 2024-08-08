from datetime import datetime
from unittest import mock

import pandas as pd

from app.endpoints.solar.solar_sales import parse_request, sales


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


def test_sales():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1, "location": 1, "groupBy": "hour"}'
    # mock calculate_co2_avoided
    with mock.patch("app.endpoints.solar.solar_sales.calculate_co2_avoided") as mock_calculate_co2_avoided:
        mock_calculate_co2_avoided.return_value = pd.DataFrame({
            "from": [datetime(2021, 1, 1, 0, 0, 0),
                     datetime(2021, 1, 1, 1, 0, 0),
                     datetime(2021, 1, 1, 2, 0, 0)],
            "to": [datetime(2021, 1, 1, 0, 59, 59),
                   datetime(2021, 1, 1, 1, 59, 59),
                   datetime(2021, 1, 1, 2, 59, 59)],
            "co2_avoided": [10, 20, 30],
            "cert_generated": [1, 2, 3],
            "cert_sold": [0.5, 1, 1.5],
            "price": [100, 200, 300],
            "income": [50, 100, 150]
        })

        response = sales(param_json)

        assert response.chart.from_ == "2021/01/01 00:00:00"
        assert response.chart.to == "2021/01/02 23:59:59"
        assert response.chart.resultCode == 200
        assert response.chart.resultText == ""
        assert response.chart.groupBy == "hour"
        assert len(response.data) == 3
        assert response.data[0].from_ == "2021/01/01 00:00:00"
        assert response.data[0].to == "2021/01/01 00:59:59"
        assert response.data[0].co2Avoided == 10
        assert response.data[0].certGenerated == 1
        assert response.data[0].certSold == 0.5
        assert response.data[0].certPrice == 100
        assert response.data[0].certIncome == 50
        assert response.data[1].from_ == "2021/01/01 01:00:00"
        assert response.data[1].to == "2021/01/01 01:59:59"
