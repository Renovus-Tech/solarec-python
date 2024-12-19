from datetime import datetime
from unittest import mock

import pandas as pd

from app.endpoints.solar.solar_performance import parse_request
from app.endpoints.solar.solar_power_curve import power_curve


def test_parse_request():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1, "location": 1, "groupBy": "hour", "generators": [1, 2]}'
    request = parse_request(param_json)

    assert request.start_date == datetime(2021, 1, 1, 0, 0, 0)
    assert request.end_date == datetime(2021, 1, 2, 23, 59, 59)
    assert request.client == 1
    assert request.location == 1
    assert request.freq == "1H"
    assert request.group_by == "hour"


def test_parse_request_no_group_by():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1, "location": 1, "generators": [1, 2]}'
    request = parse_request(param_json)

    assert request.start_date == datetime(2021, 1, 1, 0, 0, 0)
    assert request.end_date == datetime(2021, 1, 2, 23, 59, 59)
    assert request.client == 1
    assert request.location == 1
    assert request.freq == "100Y"
    assert request.group_by == None


def test_power_curve():

    with mock.patch("app.endpoints.solar.solar_power_curve.Solar") as mock_solar:
        param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1, "location": 1, "generators": [1, 2]}'
        mock_solar_instance = mock_solar.return_value
        mock_solar_instance.data = pd.DataFrame({
            "ac_production": [10, 20, 30, 12, 22, 32],
            "irradiation": [0.1, 0.2, 0.3, 0.1, 0.2, 0.3],
            "gen_id": [1, 1, 1, 2, 2, 2],
            "timestamp": [datetime(2021, 1, 1, 0, 0, 0), datetime(2021, 1, 1, 1, 0, 0), datetime(2021, 1, 1, 2, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0), datetime(2021, 1, 1, 1, 0, 0), datetime(2021, 1, 1, 2, 0, 0)]
        })
        mock_solar_instance.data.set_index(["gen_id", "timestamp"], inplace=True)

        mock_solar_instance.gen_names = ["gen1", "gen2"]
        mock_solar_instance.gen_codes = ["code1", "code2"]

        mock_solar_instance.fetch_data.return_value = None

        response = power_curve(param_json)

        assert response.chart.from_ == "2021-01-01 00:00:00"
        assert response.chart.to == "2021-01-02 23:59:59"
        assert response.chart.resultCode == 200
        assert response.chart.resultText == ""
        assert len(response.generator) == 2
        assert response.generator[0].id == 1
        assert response.generator[0].name == "gen1"
        assert response.generator[0].code == "code1"
        assert response.generator[0].data.curves.power == [40.0, 80.0, 120.0]
        assert response.generator[0].data.curves.irradiation == [0.4, 0.8, 1.2]
        assert response.generator[0].data.curves.timestamps == ["2021-01-01 00:00:00", "2021-01-01 01:00:00", "2021-01-01 02:00:00"]
        assert response.generator[0].data.medians.power == [40.0, 80.0, 120.0]
        assert response.generator[0].data.medians.irradiation == [0.3, 0.7, 1.1]
        assert response.generator[1].id == 2
        assert response.generator[1].name == "gen2"
        assert response.generator[1].code == "code2"
        assert response.generator[1].data.curves.power == [48.0, 88.0, 128.0]
        assert response.generator[0].data.curves.irradiation == [0.4, 0.8, 1.2]
        assert response.generator[1].data.curves.timestamps == ["2021-01-01 00:00:00", "2021-01-01 01:00:00", "2021-01-01 02:00:00"]
        assert response.generator[1].data.medians.power == [48.0, 88.0, 128.0]
        assert response.generator[0].data.medians.irradiation == [0.3, 0.7, 1.1]
