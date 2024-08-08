from datetime import datetime
from unittest import mock

import pandas as pd

from app.endpoints.solar.solar_performance import performance
from app.endpoints.solar.solar_sales import parse_request


def test_parse_request():
    param_json = '{"from": "2021/01/01T00:00:00", "to": "2021/01/02T00:00:00", "client": 1, "location": 1, "groupBy": "hour"}'
    request = parse_request(param_json)

    assert request.start_date == datetime(2021, 1, 1, 0, 0, 0)
    assert request.end_date == datetime(2021, 1, 2, 23, 59, 59)
    assert request.client == 1
    assert request.location == 1
    assert request.freq == "1H"
    assert request.group_by == "hour"


def test_parse_request_no_group_by():
    param_json = '{"from": "2021/01/01T00:00:00", "to": "2021/01/02T00:00:00", "client": 1, "location": 1}'
    request = parse_request(param_json)

    assert request.start_date == datetime(2021, 1, 1, 0, 0, 0)
    assert request.end_date == datetime(2021, 1, 2, 23, 59, 59)
    assert request.client == 1
    assert request.location == 1
    assert request.freq == "100Y"
    assert request.group_by == None


def test_performance():
    with mock.patch("app.endpoints.solar.solar_performance.Solar") as mock_solar:
        param_json = '{"from": "2021/01/01T00:00:00", "to": "2021/01/02T00:00:00", "client": 1, "location": 1, "generators": [1, 2]}'
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
            "irradiation": [0.1, 0.2, 0.3],
            "performance_ratio": [0.9, 0.8, 0.7],
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
            "irradiation": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            "performance_ratio": [0.9, 0.8, 0.7, 0.6, 0.5, 0.4],
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
        mock_solar_instance.gen_codes_and_names.set_index("gen_id", inplace=True)
        mock_solar_instance.fetch_data.return_value = None

        response = performance(param_json)

        assert response.chart.from_ == "2021/01/01 00:00:00"
        assert response.chart.to == "2021/01/02 23:59:59"
        assert response.chart.resultCode == 200
        assert response.chart.resultText == ""
        assert len(response.data) == 3
        assert response.data[0].from_ == "2021/01/01 00:00:00"
        assert response.data[0].to == "2021/01/01 00:59:59"
        assert response.data[0].totalProductionMwh == 10
        assert response.data[0].totalACProductionMwh == 10
        assert response.data[0].totalIrradiationKwhM2 == 0.1
        assert response.data[0].performanceRatio == 0.9
        assert response.data[0].timeBasedAvailability == 0.9
        assert len(response.data[0].genData) == 2
        assert response.data[0].genData[0].id == 1
        assert response.data[0].genData[0].name == "gen1"
        assert response.data[0].genData[0].code == "code1"
        assert response.data[0].genData[0].productionMwh == 10
        assert response.data[0].genData[0].acProductionMwh == 10
        assert response.data[0].genData[0].irradiationKwhM2 == 0.1
        assert response.data[0].genData[0].performanceRatio == 0.9
        assert response.data[0].genData[0].timeBasedAvailability == 0.9
        assert response.data[0].genData[1].id == 2
        assert response.data[0].genData[1].name == "gen2"
        assert response.data[0].genData[1].code == "code2"
        assert response.data[0].genData[1].productionMwh == 40
        assert response.data[0].genData[1].acProductionMwh == 40
        assert response.data[0].genData[1].irradiationKwhM2 == 0.4
        assert response.data[0].genData[1].performanceRatio == 0.6
        assert response.data[0].genData[1].timeBasedAvailability == 0.6

        assert response.data[1].from_ == "2021/01/01 01:00:00"
        assert response.data[1].to == "2021/01/01 01:59:59"
        assert response.data[1].totalProductionMwh == 20
        assert response.data[1].totalACProductionMwh == 20
        assert response.data[1].totalIrradiationKwhM2 == 0.2
        assert response.data[1].performanceRatio == 0.8
        assert response.data[1].timeBasedAvailability == 0.8
        assert len(response.data[1].genData) == 2
        assert response.data[1].genData[0].id == 1
        assert response.data[1].genData[0].name == "gen1"
        assert response.data[1].genData[0].code == "code1"
        assert response.data[1].genData[0].productionMwh == 20
        assert response.data[1].genData[0].acProductionMwh == 20
        assert response.data[1].genData[0].irradiationKwhM2 == 0.2
        assert response.data[1].genData[0].performanceRatio == 0.8
        assert response.data[1].genData[0].timeBasedAvailability == 0.8
        assert response.data[1].genData[1].id == 2
        assert response.data[1].genData[1].name == "gen2"
        assert response.data[1].genData[1].code == "code2"
        assert response.data[1].genData[1].productionMwh == 50
        assert response.data[1].genData[1].acProductionMwh == 50
        assert response.data[1].genData[1].irradiationKwhM2 == 0.5
        assert response.data[1].genData[1].performanceRatio == 0.5
        assert response.data[1].genData[1].timeBasedAvailability == 0.5

        assert response.data[2].from_ == "2021/01/01 02:00:00"
        assert response.data[2].to == "2021/01/01 02:59:59"
        assert response.data[2].totalProductionMwh == 30
        assert response.data[2].totalACProductionMwh == 30
        assert response.data[2].totalIrradiationKwhM2 == 0.3
        assert response.data[2].performanceRatio == 0.7
        assert response.data[2].timeBasedAvailability == 0.7
        assert len(response.data[2].genData) == 2
        assert response.data[2].genData[0].id == 1
        assert response.data[2].genData[0].name == "gen1"
        assert response.data[2].genData[0].code == "code1"
        assert response.data[2].genData[0].productionMwh == 30
        assert response.data[2].genData[0].acProductionMwh == 30
        assert response.data[2].genData[0].irradiationKwhM2 == 0.3
        assert response.data[2].genData[0].performanceRatio == 0.7
        assert response.data[2].genData[0].timeBasedAvailability == 0.7
        assert response.data[2].genData[1].id == 2
        assert response.data[2].genData[1].name == "gen2"
        assert response.data[2].genData[1].code == "code2"
        assert response.data[2].genData[1].productionMwh == 60
        assert response.data[2].genData[1].acProductionMwh == 60
        assert response.data[2].genData[1].irradiationKwhM2 == 0.6
        assert response.data[2].genData[1].performanceRatio == 0.4
        assert response.data[2].genData[1].timeBasedAvailability == 0.4
