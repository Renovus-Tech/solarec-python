from datetime import datetime
from unittest import mock

import pandas as pd
import pytest

from app.endpoints.solar.solar_alerts import parse_request, process_alerts


def test_parse_request():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1, "location": 1, "generator": 1, "data_pro_id": 1}'
    request = parse_request(param_json)

    assert request.start_date == datetime(2021, 1, 1, 0, 0, 0)
    assert request.end_date == datetime(2021, 1, 2, 23, 59, 59)
    assert request.client == 1
    assert request.location == 1
    assert request.data_pro_id == 1


def test_parse_request_with_data_pro_id():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "data_pro_id": 1}'
    request = parse_request(param_json)

    assert request.start_date == datetime(2021, 1, 1, 0, 0, 0)
    assert request.end_date == datetime(2021, 1, 2, 23, 59, 59)
    assert request.client is None
    assert request.location is None
    assert request.data_pro_id == 1


def test_parse_request_should_fail():
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "client": 1}'
    with pytest.raises(ValueError) as exception:
        parse_request(param_json)
    assert exception.value.args[0] == "Invalid parameters: either data_pro_id or client and location must be provided"


@mock.patch("app.endpoints.solar.solar_alerts.calculate_alerts")
def test_process_alerts(mock_calculate_alerts):
    param_json = '{"from": "2021-01-01T00:00:00", "to": "2021-01-02T00:00:00", "data_pro_id": 1}'
    mock_calculate_alerts.return_value = (1,
                                          1,
                                          [1],
                                          datetime(2021, 1, 1, 0, 0, 0),
                                          datetime(2021, 1, 2, 23, 59, 59),
                                          10)

    response = process_alerts(param_json)

    assert response.data.from_ == "2021-01-01 00:00"
    assert response.data.to == "2021-01-02 23:59"
    assert response.data.count == 10
    assert response.data.client == 1
    assert response.data.location == 1
    assert response.data.generators == [1]
