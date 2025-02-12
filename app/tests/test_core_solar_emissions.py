from datetime import datetime
from unittest import mock

import numpy as np
import pandas as pd

from app.core.solar_emissions import Solar, calculate_co2_avoided


@mock.patch("app.core.solar_emissions.get_co2_emissions_tons_per_Mwh")
@mock.patch("app.core.solar_emissions.get_client_settings")
def test_calculate_co2_avoided(mock_get_client_settings, mock_get_co2_emissions_per_kwh):
    mock_get_co2_emissions_per_kwh.return_value = 10
    client_settings_df = pd.DataFrame({"cli_set_value": [10, 20], "cli_set_name": ["certSoldPorcentage", "certPrice"]})
    client_settings_df.set_index("cli_set_name", inplace=True)
    mock_get_client_settings.return_value = client_settings_df

    with mock.patch("app.core.solar_emissions.Solar") as mock_solar:
        mock_solar_instance = mock_solar.return_value
        mock_solar_instance.freq = "1H"
        mock_solar_instance.data_freq = "15T"
        mock_solar_instance.datetime_end = datetime(2021, 1, 1, 23, 59, 59)
        mock_solar_instance.fetch_aggregated_by_loc_and_period.return_value = None
        data_aggregated_by_loc_and_period = pd.DataFrame({
            "power": [1, 1],
            "from": [datetime(2021, 1, 1, 0, 0), datetime(2021, 1, 1, 0, 15)],
            "cert_generated": [1, 1],
            "cert_sold": [1, 1],
            "data_date": [datetime(2021, 1, 1, 0, 0), datetime(2021, 1, 1, 0, 15)]
        })
        data_aggregated_by_loc_and_period.set_index("data_date", inplace=True)
        mock_solar_instance.data_aggregated_by_loc_and_period = data_aggregated_by_loc_and_period

        df = calculate_co2_avoided(1, 1, datetime(2021, 1, 1, 0, 0), datetime(2021, 1, 1, 1, 0), "1H", "15T")

        assert df is not None
        assert df["co2_avoided"].sum() == 20
        assert df["cert_sold"].sum() == 0.2
        assert df["cert_generated"].sum() == 2
        assert df["price"].sum() == 40
        assert df["income"].sum() == 4
        assert df["from"].iloc[0] == datetime(2021, 1, 1)
