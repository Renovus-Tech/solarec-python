from unittest import mock

from fastapi import HTTPException
import pytest
from app.nlp.mock_client import MockClient
from db.models import Location
from app.endpoints.solar.solar_onboard_location import parse_request, onboard_location


def test_parse_request():
    param_json = '{"location":21, "client":12, "text":"{\\"address\\":\\"Maldonado, Uruguay\\", \\"capacity\\":50, \\"installation_date\\":\\"2023-12-08 23:44:59.993\\"}"}'
    request = parse_request(param_json)

    assert request.client_id == 12
    assert request.location_id == 21
    assert request.text == '{\"address\":\"Maldonado, Uruguay\", \"capacity\":50, \"installation_date\":\"2023-12-08 23:44:59.993\"}'


def test_onboard_location_should_success():
    param_json = '{"location":21, "client":12, "text":"{\\"address\\":\\"Maldonado, Uruguay\\", \\"capacity\\":50, \\"installation_date\\":\\"2023-12-08 23:44:59.993\\"}"}'
    with mock.patch("app.endpoints.solar.solar_onboard_location.get_location") as mock_get_location:
        mock_get_location.return_value = Location(loc_id_auto=21, cli_id=12)

        with mock.patch("app.endpoints.solar.solar_onboard_location.update_location") as mock_update_location:

            with mock.patch('app.endpoints.solar.solar_onboard_location.LLMClientFactory.create_llm_client') as mock_create_llm_client:
                mock_create_llm_client.return_value = MockClient()

                response = onboard_location(param_json)

                assert response.client_id == 12
                assert response.location_id == 21
                assert response.address == "Maldonado, Uruguay"
                assert response.capacity == 50
                assert response.installation_date == "2023-12-08 23:44:59.993"

                assert mock_update_location.called


def test_onboard_location_should_fail_no_location():
    param_json = '{"location":21, "client":12, "text":"{\\"address\\":\\"Maldonado, Uruguay\\", \\"capacity\\":50, \\"installation_date\\":\\"2023-12-08 23:44:59.993\\"}"}'
    with mock.patch("app.endpoints.solar.solar_onboard_location.get_location") as mock_get_location:
        mock_get_location.return_value = None

        with pytest.raises(HTTPException) as exception:
            onboard_location(param_json)
        assert exception.value.status_code == 404
        assert exception.value.detail == f"No Location was found for the location ID: 21 and client ID: 12"


def test_onboard_location_should_success_no_address():
    param_json = '{"location":21, "client":12, "text":"{\\"capacity\\":50, \\"installation_date\\":\\"2023-12-08 23:44:59.993\\"}"}'
    with mock.patch("app.endpoints.solar.solar_onboard_location.get_location") as mock_get_location:
        mock_get_location.return_value = Location(loc_id_auto=21, cli_id=12)

        with mock.patch("app.endpoints.solar.solar_onboard_location.update_location") as mock_update_location:

            with mock.patch('app.endpoints.solar.solar_onboard_location.LLMClientFactory.create_llm_client') as mock_create_llm_client:
                mock_create_llm_client.return_value = MockClient()

                response = onboard_location(param_json)

                assert response.client_id == 12
                assert response.location_id == 21
                assert response.address is None
                assert response.capacity == 50
                assert response.installation_date == "2023-12-08 23:44:59.993"

                assert mock_update_location.called
