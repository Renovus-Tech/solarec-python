from datetime import datetime
from unittest import mock

import numpy as np
import pandas as pd

from app.core.solar import Solar


@mock.patch("app.core.solar.get_gen_ids_by_loc_id")
@mock.patch("app.core.solar.get_sta_id_by_loc_id")
@mock.patch("app.core.solar.get_loc_output_capacity")
@mock.patch("app.core.solar.get_gen_codes_and_names")
def test_solar_initialize(mock_get_gen_codes_and_names, mock_get_loc_output_capacity, mock_get_sta_id_by_loc_id, mock_get_gen_ids_by_loc_id):

    mock_get_gen_ids_by_loc_id.return_value = pd.DataFrame({
        "gen_id_auto": [1, 2, 3]
    })

    mock_get_sta_id_by_loc_id.return_value = pd.DataFrame({
        "sta_id_auto": [1, 2, 3]
    })

    mock_get_loc_output_capacity.return_value = 1000
    mock_get_gen_codes_and_names.return_value = pd.DataFrame({
        "gen_id_auto": [1, 2, 3],
        "gen_code": ["code_1", "code_2", "code_3"],
        "gen_name": ["name_1", "name_2", "name_3"],
        "gen_rate_power": [1000, 2000, 3000]
    })

    solar = Solar(1, 1, None, None, datetime(2021, 1, 1), datetime(2021, 1, 2), "1H")

    assert solar.loc_id == 1
    assert solar.gen_ids == [1, 2, 3]
    assert solar.sta_id == 1
    assert solar.datetime_start == datetime(2021, 1, 1)
    assert solar.datetime_end == datetime(2021, 1, 2)
    assert solar.data is None
    assert solar.cli_id == 1
    assert solar.freq == "1H"
    assert solar.loc_total_capacity == 1000
    assert solar.gen_codes_and_names is not None
    assert solar.gen_codes == ["code_1", "code_2", "code_3"]
    assert solar.gen_names == ["name_1", "name_2", "name_3"]
    assert solar.data_grouped_by_loc is None
    assert solar.gen_data is None
    assert solar.sta_data is None
    assert solar.data is None
    assert solar.data_aggregated_by_period is None
    assert solar.data_aggregated_by_loc_and_period is None


@mock.patch("app.core.solar.get_gen_ids_by_loc_id")
@mock.patch("app.core.solar.get_sta_id_by_loc_id")
@mock.patch("app.core.solar.get_loc_output_capacity")
@mock.patch("app.core.solar.get_gen_codes_and_names")
@mock.patch("app.core.solar.get_gen_datas_grouped")
@mock.patch("app.core.solar.get_sta_datas_grouped")
def test_solar_fetch_data(mock_get_sta_datas_grouped, mock_get_gen_datas_grouped, mock_get_gen_codes_and_names, mock_get_loc_output_capacity, mock_get_sta_id_by_loc_id, mock_get_gen_ids_by_loc_id):

    mock_get_gen_ids_by_loc_id.return_value = pd.DataFrame({
        "gen_id_auto": [1, 2]
    })

    mock_get_sta_id_by_loc_id.return_value = pd.DataFrame({
        "sta_id_auto": [1, 2]
    })

    mock_get_loc_output_capacity.return_value = 1000
    mock_get_gen_codes_and_names.return_value = pd.DataFrame({
        "gen_id_auto": [1, 2],
        "gen_code": ["code_1", "code_2"],
        "gen_name": ["name_1", "name_2"],
        "gen_rate_power": [1000, 2000]
    })

    gen_datas_return_value = pd.DataFrame({
        "gen_id": [1, 1, 2, 2],
        "data_date": [datetime(2021, 1, 1, 0, 0, 0),
                      datetime(2021, 1, 1, 0, 15, 0),
                      datetime(2021, 1, 1, 0, 15, 0),
                      datetime(2021, 1, 1, 0, 30, 0)],
        "power": [10, 20, 30, 40],
        "ac_production": [15, 25, 35, 45],
        "ac_production_prediction": [11, 22, 33, 44]
    })
    gen_datas_return_value.set_index(["gen_id", "data_date"], inplace=True)
    mock_get_gen_datas_grouped.return_value = gen_datas_return_value

    sta_datas_return_value = pd.DataFrame({
        "sta_id": [1, 1, 1],
        "data_date": [datetime(2021, 1, 1, 0, 0, 0),
                      datetime(2021, 1, 1, 0, 15, 0),
                      datetime(2021, 1, 1, 0, 30, 0)],
        "avg_ambient_temp": [1, 2, 3],
        "avg_module_temp": [10, 20, 30],
        "irradiation": [50, 60, 70]
    })
    sta_datas_return_value.set_index(["data_date", "sta_id"], inplace=True)
    mock_get_sta_datas_grouped.return_value = sta_datas_return_value

    solar = Solar(1, 1, None, None, datetime(2021, 1, 1, 0, 0, 0), datetime(2021, 1, 1, 0, 45, 0), "1H")
    solar.fetch_data()

    assert solar.data is not None
    assert solar.gen_data is not None
    assert solar.sta_data is not None

    assert (1, pd.Timestamp('2021-01-01 00:00:00')) in solar.data.index
    assert (2, pd.Timestamp('2021-01-01 00:00:00')) in solar.data.index
    assert (1, pd.Timestamp('2021-01-01 00:15:00')) in solar.data.index
    assert (2, pd.Timestamp('2021-01-01 00:15:00')) in solar.data.index
    assert (1, pd.Timestamp('2021-01-01 00:30:00')) in solar.data.index
    assert (2, pd.Timestamp('2021-01-01 00:30:00')) in solar.data.index

    assert solar.data["power"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 0.0025
    assert solar.data["ac_production"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 0.00375
    assert solar.data["ac_production_prediction"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 0.00275
    assert solar.data["avg_ambient_temp"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 1.0
    assert solar.data["avg_module_temp"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 10.0
    assert solar.data["irradiation"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 12.5
    assert solar.data["time_based_availability"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == False
    assert solar.data["is_missing"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 0

    assert solar.data["power"].loc[(1, pd.Timestamp('2021-01-01 00:15:00'))] == 0.005
    assert solar.data["ac_production"].loc[(1, pd.Timestamp('2021-01-01 00:15:00'))] == 0.00625
    assert solar.data["ac_production_prediction"].loc[(1, pd.Timestamp('2021-01-01 00:15:00'))] == 0.0055
    assert solar.data["avg_ambient_temp"].loc[(1, pd.Timestamp('2021-01-01 00:15:00'))] == 2.0
    assert solar.data["avg_module_temp"].loc[(1, pd.Timestamp('2021-01-01 00:15:00'))] == 20.0
    assert solar.data["irradiation"].loc[(1, pd.Timestamp('2021-01-01 00:15:00'))] == 15.0
    assert solar.data["time_based_availability"].loc[(1, pd.Timestamp('2021-01-01 00:15:00'))] == False
    assert solar.data["is_missing"].loc[(1, pd.Timestamp('2021-01-01 00:15:00'))] == 0

    assert np.isnan(solar.data["power"].loc[(1, pd.Timestamp('2021-01-01 00:30:00'))])
    assert np.isnan(solar.data["ac_production"].loc[(1, pd.Timestamp('2021-01-01 00:30:00'))])
    assert np.isnan(solar.data["ac_production_prediction"].loc[(1, pd.Timestamp('2021-01-01 00:30:00'))])
    assert solar.data["avg_ambient_temp"].loc[(1, pd.Timestamp('2021-01-01 00:30:00'))] == 3.0
    assert solar.data["avg_module_temp"].loc[(1, pd.Timestamp('2021-01-01 00:30:00'))] == 30.0
    assert solar.data["irradiation"].loc[(1, pd.Timestamp('2021-01-01 00:30:00'))] == 17.5
    assert solar.data["time_based_availability"].loc[(1, pd.Timestamp('2021-01-01 00:30:00'))] == False
    assert solar.data["is_missing"].loc[(1, pd.Timestamp('2021-01-01 00:30:00'))] == 1

    assert np.isnan(solar.data["power"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))])
    assert np.isnan(solar.data["ac_production"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))])
    assert np.isnan(solar.data["ac_production_prediction"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))])
    assert solar.data["avg_ambient_temp"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == 1.0
    assert solar.data["avg_module_temp"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == 10.0
    assert solar.data["irradiation"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == 12.5
    assert solar.data["time_based_availability"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == False
    assert solar.data["is_missing"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == 1

    assert solar.data["power"].loc[(2, pd.Timestamp('2021-01-01 00:15:00'))] == 0.0075
    assert solar.data["ac_production"].loc[(2, pd.Timestamp('2021-01-01 00:15:00'))] == 0.00875
    assert solar.data["ac_production_prediction"].loc[(2, pd.Timestamp('2021-01-01 00:15:00'))] == 0.00825
    assert solar.data["avg_ambient_temp"].loc[(2, pd.Timestamp('2021-01-01 00:15:00'))] == 2.0
    assert solar.data["avg_module_temp"].loc[(2, pd.Timestamp('2021-01-01 00:15:00'))] == 20.0
    assert solar.data["irradiation"].loc[(2, pd.Timestamp('2021-01-01 00:15:00'))] == 15.0
    assert solar.data["time_based_availability"].loc[(2, pd.Timestamp('2021-01-01 00:15:00'))] == False
    assert solar.data["is_missing"].loc[(2, pd.Timestamp('2021-01-01 00:15:00'))] == 0

    assert solar.data["power"].loc[(2, pd.Timestamp('2021-01-01 00:30:00'))] == 0.01
    assert solar.data["ac_production"].loc[(2, pd.Timestamp('2021-01-01 00:30:00'))] == 0.01125
    assert solar.data["ac_production_prediction"].loc[(2, pd.Timestamp('2021-01-01 00:30:00'))] == 0.011
    assert solar.data["avg_ambient_temp"].loc[(2, pd.Timestamp('2021-01-01 00:30:00'))] == 3.0
    assert solar.data["avg_module_temp"].loc[(2, pd.Timestamp('2021-01-01 00:30:00'))] == 30.0
    assert solar.data["irradiation"].loc[(2, pd.Timestamp('2021-01-01 00:30:00'))] == 17.5
    assert solar.data["time_based_availability"].loc[(2, pd.Timestamp('2021-01-01 00:30:00'))] == False
    assert solar.data["is_missing"].loc[(2, pd.Timestamp('2021-01-01 00:30:00'))] == 0


@mock.patch("app.core.solar.get_gen_ids_by_loc_id")
@mock.patch("app.core.solar.get_sta_id_by_loc_id")
@mock.patch("app.core.solar.get_loc_output_capacity")
@mock.patch("app.core.solar.get_gen_codes_and_names")
@mock.patch("app.core.solar.get_gen_datas_grouped")
@mock.patch("app.core.solar.get_sta_datas_grouped")
def test_solar_fetch_aggregated_by_period(mock_get_sta_datas_grouped, mock_get_gen_datas_grouped, mock_get_gen_codes_and_names, mock_get_loc_output_capacity, mock_get_sta_id_by_loc_id, mock_get_gen_ids_by_loc_id):

    mock_get_gen_ids_by_loc_id.return_value = pd.DataFrame({
        "gen_id_auto": [1, 2]
    })

    mock_get_sta_id_by_loc_id.return_value = pd.DataFrame({
        "sta_id_auto": [1, 2]
    })

    mock_get_loc_output_capacity.return_value = 1000
    mock_get_gen_codes_and_names.return_value = pd.DataFrame({
        "gen_id_auto": [1, 2],
        "gen_code": ["code_1", "code_2"],
        "gen_name": ["name_1", "name_2"],
        "gen_rate_power": [1000, 2000]
    }, index=[1, 2])

    gen_datas_return_value = pd.DataFrame({
        "gen_id": [1, 1, 2, 2],
        "data_date": [datetime(2021, 1, 1, 0, 0, 0),
                      datetime(2021, 1, 1, 0, 15, 0),
                      datetime(2021, 1, 1, 0, 15, 0),
                      datetime(2021, 1, 1, 0, 30, 0)],
        "power": [10, 20, 30, 40],
        "ac_production": [15, 25, 35, 45],
        "ac_production_prediction": [11, 22, 33, 44]
    })
    gen_datas_return_value.set_index(["gen_id", "data_date"], inplace=True)
    mock_get_gen_datas_grouped.return_value = gen_datas_return_value

    sta_datas_return_value = pd.DataFrame({
        "sta_id": [1, 1, 1],
        "data_date": [datetime(2021, 1, 1, 0, 0, 0),
                      datetime(2021, 1, 1, 0, 15, 0),
                      datetime(2021, 1, 1, 0, 30, 0)],
        "avg_ambient_temp": [1, 2, 3],
        "avg_module_temp": [10, 20, 30],
        "irradiation": [50, 60, 70]
    })
    sta_datas_return_value.set_index(["data_date", "sta_id"], inplace=True)
    mock_get_sta_datas_grouped.return_value = sta_datas_return_value

    solar = Solar(1, 1, None, None, datetime(2021, 1, 1, 0, 0, 0), datetime(2021, 1, 1, 2, 0, 0), "1H")
    solar.fetch_aggregated_by_period()

    assert solar.data_aggregated_by_period is not None
    assert (1, pd.Timestamp('2021-01-01 00:00:00')) in solar.data_aggregated_by_period.index
    assert (1, pd.Timestamp('2021-01-01 01:00:00')) in solar.data_aggregated_by_period.index
    assert (2, pd.Timestamp('2021-01-01 00:00:00')) in solar.data_aggregated_by_period.index
    assert (2, pd.Timestamp('2021-01-01 01:00:00')) in solar.data_aggregated_by_period.index

    assert solar.data_aggregated_by_period["power"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 0.0075
    assert solar.data_aggregated_by_period["ac_production"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 0.01
    assert solar.data_aggregated_by_period["ac_production_prediction"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 0.00825
    assert solar.data_aggregated_by_period["avg_ambient_temp"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == np.mean([1, 2, 3])
    assert solar.data_aggregated_by_period["avg_module_temp"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == np.mean([10, 20, 30])
    assert solar.data_aggregated_by_period["irradiation"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 45.0
    assert solar.data_aggregated_by_period["time_based_availability"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 1
    assert solar.data_aggregated_by_period["is_missing"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 2
    assert solar.data_aggregated_by_period["specific_yield"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 0.01
    assert solar.data_aggregated_by_period["performance_ratio"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == 0.022222222222222223
    assert solar.data_aggregated_by_period["from"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == pd.Timestamp('2021-01-01 00:00:00')
    assert solar.data_aggregated_by_period["to"].loc[(1, pd.Timestamp('2021-01-01 00:00:00'))] == pd.Timestamp('2021-01-01 00:59:59')

    assert solar.data_aggregated_by_period["power"].loc[(1, pd.Timestamp('2021-01-01 01:00:00'))] == 0
    assert solar.data_aggregated_by_period["ac_production"].loc[(1, pd.Timestamp('2021-01-01 01:00:00'))] == 0
    assert solar.data_aggregated_by_period["ac_production_prediction"].loc[(1, pd.Timestamp('2021-01-01 01:00:00'))] == 0
    assert np.isnan(solar.data_aggregated_by_period["avg_ambient_temp"].loc[(1, pd.Timestamp('2021-01-01 01:00:00'))])
    assert np.isnan(solar.data_aggregated_by_period["avg_module_temp"].loc[(1, pd.Timestamp('2021-01-01 01:00:00'))])
    assert solar.data_aggregated_by_period["irradiation"].loc[(1, pd.Timestamp('2021-01-01 01:00:00'))] == 0
    assert solar.data_aggregated_by_period["time_based_availability"].loc[(1, pd.Timestamp('2021-01-01 01:00:00'))] == 1
    assert solar.data_aggregated_by_period["is_missing"].loc[(1, pd.Timestamp('2021-01-01 01:00:00'))] == 4
    assert solar.data_aggregated_by_period["specific_yield"].loc[(1, pd.Timestamp('2021-01-01 01:00:00'))] == 0
    assert solar.data_aggregated_by_period["performance_ratio"].loc[(1, pd.Timestamp('2021-01-01 01:00:00'))] == 0
    assert solar.data_aggregated_by_period["from"].loc[(1, pd.Timestamp('2021-01-01 01:00:00'))] == pd.Timestamp('2021-01-01 01:00:00')
    assert solar.data_aggregated_by_period["to"].loc[(1, pd.Timestamp('2021-01-01 01:00:00'))] == pd.Timestamp('2021-01-01 01:59:59')

    assert solar.data_aggregated_by_period["power"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == 0.0175
    assert solar.data_aggregated_by_period["ac_production"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == 0.02
    assert solar.data_aggregated_by_period["ac_production_prediction"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == 0.01925
    assert solar.data_aggregated_by_period["avg_ambient_temp"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == np.mean([1, 2, 3])
    assert solar.data_aggregated_by_period["avg_module_temp"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == np.mean([10, 20, 30])
    assert solar.data_aggregated_by_period["irradiation"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == 45.0
    assert solar.data_aggregated_by_period["time_based_availability"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == 1
    assert solar.data_aggregated_by_period["is_missing"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == 2
    assert solar.data_aggregated_by_period["specific_yield"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == 0.01
    assert solar.data_aggregated_by_period["performance_ratio"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == 0.022222222222222223
    assert solar.data_aggregated_by_period["from"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == pd.Timestamp('2021-01-01 00:00:00')
    assert solar.data_aggregated_by_period["to"].loc[(2, pd.Timestamp('2021-01-01 00:00:00'))] == pd.Timestamp('2021-01-01 00:59:59')

    assert solar.data_aggregated_by_period["power"].loc[(2, pd.Timestamp('2021-01-01 01:00:00'))] == 0
    assert solar.data_aggregated_by_period["ac_production"].loc[(2, pd.Timestamp('2021-01-01 01:00:00'))] == 0
    assert solar.data_aggregated_by_period["ac_production_prediction"].loc[(2, pd.Timestamp('2021-01-01 01:00:00'))] == 0
    assert np.isnan(solar.data_aggregated_by_period["avg_ambient_temp"].loc[(2, pd.Timestamp('2021-01-01 01:00:00'))])
    assert np.isnan(solar.data_aggregated_by_period["avg_module_temp"].loc[(2, pd.Timestamp('2021-01-01 01:00:00'))])
    assert solar.data_aggregated_by_period["irradiation"].loc[(2, pd.Timestamp('2021-01-01 01:00:00'))] == 0
    assert solar.data_aggregated_by_period["time_based_availability"].loc[(2, pd.Timestamp('2021-01-01 01:00:00'))] == 1
    assert solar.data_aggregated_by_period["is_missing"].loc[(2, pd.Timestamp('2021-01-01 01:00:00'))] == 4
    assert solar.data_aggregated_by_period["specific_yield"].loc[(2, pd.Timestamp('2021-01-01 01:00:00'))] == 0
    assert solar.data_aggregated_by_period["performance_ratio"].loc[(2, pd.Timestamp('2021-01-01 01:00:00'))] == 0
    assert solar.data_aggregated_by_period["from"].loc[(2, pd.Timestamp('2021-01-01 01:00:00'))] == pd.Timestamp('2021-01-01 01:00:00')
    assert solar.data_aggregated_by_period["to"].loc[(2, pd.Timestamp('2021-01-01 01:00:00'))] == pd.Timestamp('2021-01-01 01:59:59')


@mock.patch("app.core.solar.get_gen_ids_by_loc_id")
@mock.patch("app.core.solar.get_sta_id_by_loc_id")
@mock.patch("app.core.solar.get_loc_output_capacity")
@mock.patch("app.core.solar.get_gen_codes_and_names")
@mock.patch("app.core.solar.get_gen_datas_grouped")
@mock.patch("app.core.solar.get_sta_datas_grouped")
def test_solar_fetch_aggregated_by_loc_and_period(mock_get_sta_datas_grouped, mock_get_gen_datas_grouped, mock_get_gen_codes_and_names, mock_get_loc_output_capacity, mock_get_sta_id_by_loc_id, mock_get_gen_ids_by_loc_id):

    mock_get_gen_ids_by_loc_id.return_value = pd.DataFrame({
        "gen_id_auto": [1, 2]
    })

    mock_get_sta_id_by_loc_id.return_value = pd.DataFrame({
        "sta_id_auto": [1, 2]
    })

    mock_get_loc_output_capacity.return_value = 1000
    mock_get_gen_codes_and_names.return_value = pd.DataFrame({
        "gen_id_auto": [1, 2],
        "gen_code": ["code_1", "code_2"],
        "gen_name": ["name_1", "name_2"],
        "gen_rate_power": [1000, 2000]
    }, index=[1, 2])

    gen_datas_return_value = pd.DataFrame({
        "gen_id": [1, 1, 2, 2],
        "data_date": [datetime(2021, 1, 1, 0, 0, 0),
                      datetime(2021, 1, 1, 0, 15, 0),
                      datetime(2021, 1, 1, 0, 15, 0),
                      datetime(2021, 1, 1, 0, 30, 0)],
        "power": [10, 20, 30, 40],
        "ac_production": [15, 25, 35, 45],
        "ac_production_prediction": [11, 22, 33, 44]
    })
    gen_datas_return_value.set_index(["gen_id", "data_date"], inplace=True)
    mock_get_gen_datas_grouped.return_value = gen_datas_return_value

    sta_datas_return_value = pd.DataFrame({
        "sta_id": [1, 1, 1],
        "data_date": [datetime(2021, 1, 1, 0, 0, 0),
                      datetime(2021, 1, 1, 0, 15, 0),
                      datetime(2021, 1, 1, 0, 30, 0)],
        "avg_ambient_temp": [1, 2, 3],
        "avg_module_temp": [10, 20, 30],
        "irradiation": [50, 60, 70]
    })
    sta_datas_return_value.set_index(["data_date", "sta_id"], inplace=True)
    mock_get_sta_datas_grouped.return_value = sta_datas_return_value

    solar = Solar(1, 1, None, None, datetime(2021, 1, 1, 0, 0, 0), datetime(2021, 1, 1, 2, 0, 0), "1H")
    solar.fetch_aggregated_by_loc_and_period()

    assert solar.data_aggregated_by_loc_and_period is not None
    assert pd.Timestamp('2021-01-01 00:00:00') in solar.data_aggregated_by_loc_and_period.index
    assert pd.Timestamp('2021-01-01 01:00:00') in solar.data_aggregated_by_loc_and_period.index

    assert solar.data_aggregated_by_loc_and_period["power"].loc[pd.Timestamp('2021-01-01 00:00:00')] == 0.025
    assert solar.data_aggregated_by_loc_and_period["ac_production"].loc[pd.Timestamp('2021-01-01 00:00:00')] == 0.03
    assert solar.data_aggregated_by_loc_and_period["ac_production_prediction"].loc[pd.Timestamp('2021-01-01 00:00:00')] == 0.0275
    assert solar.data_aggregated_by_loc_and_period["avg_ambient_temp"].loc[pd.Timestamp('2021-01-01 00:00:00')] == np.mean([1, 2, 3])
    assert solar.data_aggregated_by_loc_and_period["avg_module_temp"].loc[pd.Timestamp('2021-01-01 00:00:00')] == np.mean([10, 20, 30])
    assert solar.data_aggregated_by_loc_and_period["irradiation"].loc[pd.Timestamp('2021-01-01 00:00:00')] == 45.0
    assert solar.data_aggregated_by_loc_and_period["time_based_availability"].loc[pd.Timestamp('2021-01-01 00:00:00')] == 1
    assert solar.data_aggregated_by_loc_and_period["performance_ratio"].loc[pd.Timestamp('2021-01-01 00:00:00')] == 0.022222222222222223
    assert solar.data_aggregated_by_loc_and_period["loc_performance_ratio"].loc[pd.Timestamp('2021-01-01 00:00:00')] == 0.06666666666666667
    assert solar.data_aggregated_by_loc_and_period["loc_specific_yield"].loc[pd.Timestamp('2021-01-01 00:00:00')] == 0.03
    assert solar.data_aggregated_by_loc_and_period["specific_yield"].loc[pd.Timestamp('2021-01-01 00:00:00')] == 0.02
    assert solar.data_aggregated_by_loc_and_period["from"].loc[pd.Timestamp('2021-01-01 00:00:00')] == pd.Timestamp('2021-01-01 00:00:00')
    assert solar.data_aggregated_by_loc_and_period["to"].loc[pd.Timestamp('2021-01-01 00:00:00')] == pd.Timestamp('2021-01-01 00:59:59')

    assert solar.data_aggregated_by_loc_and_period["power"].loc[pd.Timestamp('2021-01-01 01:00:00')] == 0
    assert solar.data_aggregated_by_loc_and_period["ac_production"].loc[pd.Timestamp('2021-01-01 01:00:00')] == 0
    assert solar.data_aggregated_by_loc_and_period["ac_production_prediction"].loc[pd.Timestamp('2021-01-01 01:00:00')] == 0
    assert solar.data_aggregated_by_loc_and_period["avg_ambient_temp"].loc[pd.Timestamp('2021-01-01 01:00:00')] == 0
    assert solar.data_aggregated_by_loc_and_period["avg_module_temp"].loc[pd.Timestamp('2021-01-01 01:00:00')] == 0
    assert solar.data_aggregated_by_loc_and_period["irradiation"].loc[pd.Timestamp('2021-01-01 01:00:00')] == 0
    assert solar.data_aggregated_by_loc_and_period["time_based_availability"].loc[pd.Timestamp('2021-01-01 01:00:00')] == 1
    assert solar.data_aggregated_by_loc_and_period["performance_ratio"].loc[pd.Timestamp('2021-01-01 01:00:00')] == 0
    assert solar.data_aggregated_by_loc_and_period["loc_performance_ratio"].loc[pd.Timestamp('2021-01-01 01:00:00')] == 0
    assert solar.data_aggregated_by_loc_and_period["loc_specific_yield"].loc[pd.Timestamp('2021-01-01 01:00:00')] == 0
    assert solar.data_aggregated_by_loc_and_period["specific_yield"].loc[pd.Timestamp('2021-01-01 01:00:00')] == 0
    assert solar.data_aggregated_by_loc_and_period["from"].loc[pd.Timestamp('2021-01-01 01:00:00')] == pd.Timestamp('2021-01-01 01:00:00')
    assert solar.data_aggregated_by_loc_and_period["to"].loc[pd.Timestamp('2021-01-01 01:00:00')] == pd.Timestamp('2021-01-01 01:59:59')
