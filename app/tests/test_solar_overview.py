from datetime import datetime
from unittest import mock

import pandas as pd

from app.endpoints.solar.solar_overview import parse_request, overview


def test_parse_request():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1, "location": 1}'
    request = parse_request(param_json)

    assert request.start_date == datetime(2021, 1, 1, 0, 0, 0)
    assert request.end_date == datetime(2021, 1, 2, 23, 59, 59)
    assert request.client == 1
    assert request.location == 1


def test_overview():
    with mock.patch("app.endpoints.solar.solar_overview.Solar") as mock_solar:
        param_json = '{"from": "2021/01/01T00:00:00", "to": "2021/01/02T00:00:00", "client": 1, "location": 1}'
        mock_solar_instance = mock_solar.return_value
        mock_solar_instance.data = pd.DataFrame({
            "ac_production": [10, 20, 30, 12, 22, 32],
            "irradiation": [0.1, 0.2, 0.3, 0.1, 0.2, 0.3],
            "gen_id": [1, 1, 1, 2, 2, 2],
            "timestamp": ["2021/01/01 00:00:00", "2021/01/01 01:00:00", "2021/01/01 02:00:00",
                          "2021/01/01 00:00:00", "2021/01/01 01:00:00", "2021/01/01 02:00:00"]
        })
        mock_solar_instance.data.set_index(["gen_id", "timestamp"], inplace=True)
        mock_solar_instance.data_aggregated_by_loc_and_period = pd.DataFrame({
            "power": [10, 20, 30],
            "ac_production": [10, 20, 30],
            "ac_production_prediction": [12, 22, 32],
            "avg_ambient_temp": [20, 25, 30],
            "avg_module_temp": [25, 30, 35],
            "loc_specific_yield": [100, 100, 100],
            "irradiation": [0.1, 0.2, 0.3],
            "loc_performance_ratio": [0.9, 0.8, 0.7],
            "time_based_availability": [0.9, 0.8, 0.7],
            "from": [datetime(2021, 1, 1, 0, 0, 0), datetime(2021, 1, 1, 1, 0, 0), datetime(2021, 1, 1, 2, 0, 0)],
            "to": [datetime(2021, 1, 1, 0, 59, 59), datetime(2021, 1, 1, 1, 59, 59), datetime(2021, 1, 1, 2, 59, 59)],
            "gen_id": [1, 1, 1],
            "timestamp": ["2021/01/01 00:00:00", "2021/01/01 01:00:00", "2021/01/01 02:00:00"]
        })
        mock_solar_instance.data_aggregated_by_loc_and_period.set_index(["timestamp"], inplace=True)
        mock_solar_instance.data_aggregated_by_period = pd.DataFrame({
            "power": [10, 20, 30, 40, 50, 60],
            "ac_production": [10, 20, 30, 40, 50, 60],
            "ac_production_prediction": [12, 22, 32, 42, 52, 62],
            "avg_ambient_temp": [20, 25, 30, 20, 25, 30],
            "avg_module_temp": [25, 30, 35, 25, 30, 35],
            "loc_specific_yield": [100, 100, 100, 100, 100, 100],
            "irradiation": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            "loc_performance_ratio": [0.9, 0.8, 0.7, 0.6, 0.5, 0.4],
            "time_based_availability": [0.9, 0.8, 0.7, 0.6, 0.5, 0.4],
            "from": [datetime(2021, 1, 1, 0, 0, 0), datetime(2021, 1, 1, 1, 0, 0), datetime(2021, 1, 1, 2, 0, 0),
                     datetime(2021, 1, 1, 0, 0, 0), datetime(2021, 1, 1, 1, 0, 0), datetime(2021, 1, 1, 2, 0, 0)],
            "to": [datetime(2021, 1, 1, 0, 59, 59), datetime(2021, 1, 1, 1, 59, 59), datetime(2021, 1, 1, 2, 59, 59),
                   datetime(2021, 1, 1, 0, 59, 59), datetime(2021, 1, 1, 1, 59, 59), datetime(2021, 1, 1, 2, 59, 59)],
            "gen_id": [1, 1, 1, 2, 2, 2],
            "timestamp": ["2021/01/01 00:00:00", "2021/01/01 01:00:00", "2021/01/01 02:00:00",
                          "2021/01/01 00:00:00", "2021/01/01 01:00:00", "2021/01/01 02:00:00"]
        })
        mock_solar_instance.data_aggregated_by_period.set_index(["gen_id", "timestamp"], inplace=True)

        mock_solar_instance.gen_names = ["gen1", "gen2"]
        mock_solar_instance.gen_codes = ["code1", "code2"]
        mock_solar_instance.gen_codes_and_names = pd.DataFrame({
            "gen_code": ["code1", "code2"],
            "gen_name": ["gen1", "gen2"],
            "gen_id": [1, 2],
        })
        mock_solar_instance.gen_ids = [1, 2]
        mock_solar_instance.gen_codes_and_names.set_index("gen_id", inplace=True)
        mock_solar_instance.fetch_data.return_value = None

        response = overview(param_json)

        assert response.chart.from_ == "2021/01/01 00:00:00"
        assert response.chart.to == "2021/01/01 00:59:59"
        assert response.chart.resultCode == 200
        assert response.chart.resultText == ""
        assert len(response.data) == 1
        assert response.data[0].performanceRatio == 0.9
        assert response.data[0].timeBasedAvailability == 90
        assert response.data[0].specificYield == 100
        assert response.data[0].irradiationKwhM2 == 0.1
        assert response.data[0].productionMwh == 10
        assert response.data[0].avgAmbientTemp == 20
        assert response.data[0].avgModuleTemp == 25
        assert response.data[0].code == ["code1", "code2"]
        assert response.data[0].id == [1, 2]
        assert response.data[0].name == ["gen1", "gen2"]
