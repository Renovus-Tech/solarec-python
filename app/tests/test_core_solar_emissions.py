from datetime import datetime
from unittest import mock

import numpy as np
import pandas as pd

from app.core.solar_emissions import Solar, calculate_co2_avoided


@mock.patch("app.core.solar_emissions.get_co2_emissions_per_kwh")
@mock.patch("app.core.solar_emissions.get_client_settings")
def test_calculate_co2_avoided(mock_get_client_settings, mock_get_co2_emissions_per_kwh):
    co2_emissions_df = pd.DataFrame({"data_date": [datetime(2021, 1, 1, 0, 0), datetime(2021, 1, 1, 0, 15)], "co2_per_mwh": [0.5, 0.6]})
    co2_emissions_df.set_index("data_date", inplace=True)
    mock_get_co2_emissions_per_kwh.return_value = co2_emissions_df
    client_settings_df = pd.DataFrame({"cli_set_value": [10, 20], "cli_set_name": ["certSoldPorcentage", "certPrice"]})
    client_settings_df.set_index("cli_set_name", inplace=True)
    mock_get_client_settings.return_value = client_settings_df

    with mock.patch("app.core.solar_emissions.Solar") as mock_solar:
        mock_solar_instance = mock_solar.return_value
        mock_solar_instance.freq = "1H"
        mock_solar_instance.datetime_end = datetime(2021, 1, 1, 23, 59, 59)
        mock_solar_instance.fetch_aggregated_by_loc_and_period.return_value = None
        solar_data = pd.DataFrame({
            "power": [1, 1],
            "from": [datetime(2021, 1, 1, 0, 0), datetime(2021, 1, 1, 0, 15)],
            "cert_generated": [1, 1],
            "cert_sold": [1, 1],
            "data_date": [datetime(2021, 1, 1, 0, 0), datetime(2021, 1, 1, 0, 15)]
        })
        solar_data.set_index("data_date", inplace=True)
        mock_solar_instance.data = solar_data

        df = calculate_co2_avoided(1, 1, datetime(2021, 1, 1, 0, 0), datetime(2021, 1, 1, 1, 0), "1H")

        assert df is not None
        assert df["co2_avoided"].sum() == 0.5 + 0.6
        assert df["cert_sold"].sum() == 0.2
        assert df["cert_generated"].sum() == 2
        assert df["price"].sum() == 40
        assert df["income"].sum() == 4
        assert df["from"].iloc[0] == datetime(2021, 1, 1)