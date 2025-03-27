from datetime import datetime
from unittest import mock

import pandas as pd
import pytest
from db.models import CliGenAlert, GenData, Generator, Location
from db.utils import (get_client_settings, get_co2_emissions_tons_per_Mwh,
                      get_gen_codes_and_names, get_gen_datas,
                      get_gen_datas_grouped, get_gen_ids_by_data_pro_id,
                      get_gen_ids_by_loc_id, get_loc_output_capacity, get_location,
                      get_period_end, get_sta_datas, get_sta_datas_grouped,
                      get_sta_id_by_loc_id, group_by_to_pd_frequency,
                      insert_cli_gen_alerts, remove_microseconds, update_location)
from mock_alchemy.mocking import UnifiedAlchemyMagicMock


def test_get_loc_output_capacity():
    loc_id = 1
    loc_output_capacity = 1000

    session = UnifiedAlchemyMagicMock(data=[
        (
            [mock.call.query(Location.loc_output_capacity),
             mock.call.filter(Location.loc_id_auto == loc_id)],
            [[loc_output_capacity]]
        )])
    assert get_loc_output_capacity(session, loc_id) == loc_output_capacity


def test_get_period_end_1H():
    datetime_start = datetime(2021, 1, 1, 0, 0, 0)
    freq = "1H"
    end_date = datetime(2022, 1, 1, 0, 0, 0)

    result = get_period_end(datetime_start, freq, end_date)

    assert result == datetime(2021, 1, 1, 0, 59, 59)


def test_get_period_end_1D():
    datetime_start = datetime(2021, 1, 1, 0, 0, 0)
    freq = "1D"
    end_date = datetime(2022, 1, 1, 0, 0, 0)

    result = get_period_end(datetime_start, freq, end_date)

    assert result == datetime(2021, 1, 1, 23, 59, 59)


def test_get_period_end_1W_mid_week():
    datetime_start = datetime(2021, 1, 1, 0, 0, 0)
    freq = "1W"
    end_date = datetime(2022, 1, 1, 0, 0, 0)

    result = get_period_end(datetime_start, freq, end_date)

    assert result == datetime(2021, 1, 3, 23, 59, 59)


def test_get_period_end_1W_end_week():
    datetime_start = datetime(2021, 1, 4, 0, 0, 0)
    freq = "1W"
    end_date = datetime(2022, 1, 1, 0, 0, 0)

    result = get_period_end(datetime_start, freq, end_date)

    assert result == datetime(2021, 1, 10, 23, 59, 59)


def test_get_period_end_1M_start_month():
    datetime_start = datetime(2021, 1, 1, 0, 0, 0)
    freq = "1M"
    end_date = datetime(2022, 1, 1, 0, 0, 0)

    result = get_period_end(datetime_start, freq, end_date)

    assert result == datetime(2021, 1, 31, 23, 59, 59)


def test_get_period_end_1M_mid_month():
    datetime_start = datetime(2021, 1, 15, 0, 0, 0)
    freq = "1M"
    end_date = datetime(2022, 1, 1, 0, 0, 0)

    result = get_period_end(datetime_start, freq, end_date)

    assert result == datetime(2021, 1, 31, 23, 59, 59)


def test_get_period_end_1M_end_month():
    datetime_start = datetime(2021, 1, 31, 0, 0, 0)
    freq = "1M"
    end_date = datetime(2022, 1, 1, 0, 0, 0)

    result = get_period_end(datetime_start, freq, end_date)

    assert result == datetime(2021, 1, 31, 23, 59, 59)


def test_get_period_end_1Y_start_year():
    datetime_start = datetime(2021, 1, 1, 0, 0, 0)
    freq = "1Y"
    end_date = datetime(2022, 1, 1, 0, 0, 0)

    result = get_period_end(datetime_start, freq, end_date)

    assert result == datetime(2021, 12, 31, 23, 59, 59)


def test_get_period_end_1Y_mid_year():
    datetime_start = datetime(2021, 6, 1, 0, 0, 0)
    freq = "1Y"
    end_date = datetime(2022, 1, 1, 0, 0, 0)

    result = get_period_end(datetime_start, freq, end_date)

    assert result == datetime(2021, 12, 31, 23, 59, 59)


def test_get_period_end_1Y_end_year():
    datetime_start = datetime(2021, 12, 31, 0, 0, 0)
    freq = "1Y"
    end_date = datetime(2022, 1, 1, 0, 0, 0)

    result = get_period_end(datetime_start, freq, end_date)

    assert result == datetime(2021, 12, 31, 23, 59, 59)


def test_get_period_end_over_end_date():
    datetime_start = datetime(2021, 1, 1, 0, 0, 0)
    freq = "1Y"
    end_date = datetime(2021, 6, 6, 0, 0, 0)

    result = get_period_end(datetime_start, freq, end_date)

    assert result == datetime(2021, 6, 6, 23, 59, 59)


def test_get_period_end_freq_none():
    datetime_start = datetime(2021, 1, 1, 0, 0, 0)
    freq = None
    end_date = datetime(2021, 6, 6, 0, 0, 0)

    result = get_period_end(datetime_start, freq, end_date)

    assert result == end_date


def test_group_by_to_pd_frequency():

    assert group_by_to_pd_frequency("hour") == "1H"
    assert group_by_to_pd_frequency("day") == "1D"
    assert group_by_to_pd_frequency("week") == "1W"
    assert group_by_to_pd_frequency("month") == "1M"
    assert group_by_to_pd_frequency("year") == "1Y"


def test_remove_microseconds():
    df = pd.DataFrame({
        "datetime": [datetime(2021, 1, 1, 0, 0, 0, 499999),
                     datetime(2021, 1, 1, 0, 0, 0, 500000),
                     datetime(2021, 1, 1, 0, 0, 0, 500001)]
    })

    df["datetime"] = df["datetime"].apply(remove_microseconds)

    assert df["datetime"].iloc[0] == datetime(2021, 1, 1, 0, 0, 0)
    assert df["datetime"].iloc[1] == datetime(2021, 1, 1, 0, 0, 0)
    assert df["datetime"].iloc[2] == datetime(2021, 1, 1, 0, 0, 1)


def test_get_gen_datas_grouped():
    cli_id = 1
    gen_ids = [1, 2, 3]
    datetime_start = datetime(2021, 1, 1, 0, 0, 0)
    datetime_end = datetime(2021, 1, 2, 0, 0, 0)
    data_type_names = {1: "data_type_1", 2: "data_type_2", 3: "extra_column"}

    session = UnifiedAlchemyMagicMock()
    with mock.patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = pd.DataFrame({
            "gen_id": [1, 1, 2, 2, 3, 3],
            "data_date": [datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0)],
            "data_value": [10, 20, 30, 40, 50, 60],
            "data_type_id": [1, 2, 1, 2, 1, 2]
        })

        df = get_gen_datas_grouped(session, cli_id, gen_ids, datetime_start, datetime_end, '15T', data_type_names)

        assert df.shape == (3, 3)
        assert df.columns.tolist() == ["data_type_1", "data_type_2", "extra_column"]
        assert df["data_type_1"].tolist() == [10, 30, 50]
        assert df["data_type_2"].tolist() == [20, 40, 60]
        assert df["extra_column"].tolist() == [None, None, None]


def test_get_gen_codes_and_names():
    gen_ids = [1, 2, 3]
    session = UnifiedAlchemyMagicMock()

    with mock.patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = pd.DataFrame({
            "gen_id_auto": [1, 2, 3],
            "gen_code": ["code_1", "code_2", "code_3"],
            "gen_name": ["name_1", "name_2", "name_3"],
            "gen_rate_power": [1000, 2000, 3000]
        })

        df = get_gen_codes_and_names(session, gen_ids)

    assert df.shape == (3, 3)
    assert df.index.tolist() == gen_ids
    assert df.columns.tolist() == ["gen_code", "gen_name", "gen_rate_power"]
    assert df["gen_code"].tolist() == ["code_1", "code_2", "code_3"]
    assert df["gen_name"].tolist() == ["name_1", "name_2", "name_3"]
    assert df["gen_rate_power"].tolist() == [1000, 2000, 3000]


def test_get_sta_datas_grouped():
    cli_id = 1
    sta_id = 1
    datetime_start = datetime(2021, 1, 1, 0, 0, 0)
    datetime_end = datetime(2021, 1, 2, 0, 0, 0)
    data_type_names = {1: "data_type_1", 2: "data_type_2", 3: "extra_column"}
    session = UnifiedAlchemyMagicMock()
    with mock.patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = pd.DataFrame({
            "sta_id": [1, 1, 1, 1, 1, 1],
            "data_date": [datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0)],
            "data_value": [10, 20, 30, 40, 50, 60],
            "data_type_id": [1, 2, 1, 2, 1, 2]
        })

        df = get_sta_datas_grouped(session, cli_id, sta_id, datetime_start, datetime_end, '15T', data_type_names)

        assert df.shape == (1, 3)
        assert df.columns.tolist() == ["data_type_1", "data_type_2", "extra_column"]
        assert df["data_type_1"].tolist() == [10 + 30 + 50]
        assert df["data_type_2"].tolist() == [20 + 40 + 60]
        assert df["extra_column"].tolist() == [0]


def test_get_gen_datas():
    gen_ids = [1, 2, 3]
    data_type_ids = [1, 2]
    datetime_start = datetime(2021, 1, 1, 0, 0, 0)
    datetime_end = datetime(2021, 1, 2, 0, 0, 0)
    data_name = "data_value"
    session = UnifiedAlchemyMagicMock()
    with mock.patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = pd.DataFrame({
            "gen_id": [1, 1, 2, 2, 3, 3],
            "data_date": [datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0)],
            "data_value": [10, 20, 30, 40, 50, 60],
            "data_type_id": [1, 2, 1, 2, 1, 2]
        })

        df = get_gen_datas(session, gen_ids, data_type_ids, datetime_start, datetime_end, data_name)

        assert df.shape == (6, 4)
        assert df.columns.tolist() == ["gen_id", "data_date", "data_value", "data_type_id"]
        assert df["gen_id"].tolist() == [1, 1, 2, 2, 3, 3]
        assert df["data_date"].tolist() == [datetime(2021, 1, 1, 0, 0, 0),
                                            datetime(2021, 1, 1, 0, 0, 0),
                                            datetime(2021, 1, 1, 0, 0, 0),
                                            datetime(2021, 1, 1, 0, 0, 0),
                                            datetime(2021, 1, 1, 0, 0, 0),
                                            datetime(2021, 1, 1, 0, 0, 0)]
        assert df["data_value"].tolist() == [10, 20, 30, 40, 50, 60]


def test_get_sta_datas():
    sta_ids = [1, 2, 3]
    data_type_ids = [1, 2]
    datetime_start = datetime(2021, 1, 1, 0, 0, 0)
    datetime_end = datetime(2021, 1, 2, 0, 0, 0)
    data_name = "data_value"
    session = UnifiedAlchemyMagicMock()
    with mock.patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = pd.DataFrame({
            "sta_id": [1, 1, 2, 2, 3, 3],
            "data_date": [datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0)],
            "data_value": [10, 20, 30, 40, 50, 60],
            "data_type_id": [1, 2, 1, 2, 1, 2]
        })

        df = get_sta_datas(session, sta_ids, data_type_ids, datetime_start, datetime_end, data_name)

        assert df.shape == (6, 4)
        assert df.columns.tolist() == ["sta_id", "data_date", "data_value", "data_type_id"]
        assert df["sta_id"].tolist() == [1, 1, 2, 2, 3, 3]
        assert df["data_date"].tolist() == [datetime(2021, 1, 1, 0, 0, 0),
                                            datetime(2021, 1, 1, 0, 0, 0),
                                            datetime(2021, 1, 1, 0, 0, 0),
                                            datetime(2021, 1, 1, 0, 0, 0),
                                            datetime(2021, 1, 1, 0, 0, 0),
                                            datetime(2021, 1, 1, 0, 0, 0)]
        assert df["data_value"].tolist() == [10, 20, 30, 40, 50, 60]


def test_get_gen_ids_by_loc_id():
    loc_id = 1
    session = UnifiedAlchemyMagicMock()
    with mock.patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = pd.DataFrame({
            "gen_id_auto": [1, 2, 3]
        })

        df = get_gen_ids_by_loc_id(session, loc_id)

        assert df.shape == (3, 1)
        assert df["gen_id_auto"].tolist() == [1, 2, 3]


def test_get_sta_id_by_loc_id():
    loc_id = 1
    session = UnifiedAlchemyMagicMock()
    with mock.patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = pd.DataFrame({
            "sta_id_auto": [1, 2, 3]
        })

        df = get_sta_id_by_loc_id(session, loc_id)

        assert df.shape == (3, 1)
        assert df["sta_id_auto"].tolist() == [1, 2, 3]


def test_get_gen_codes_and_names():
    gen_ids = [1, 2, 3]
    session = UnifiedAlchemyMagicMock()
    with mock.patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = pd.DataFrame({
            "gen_id_auto": [1, 2, 3],
            "gen_code": ["code_1", "code_2", "code_3"],
            "gen_name": ["name_1", "name_2", "name_3"],
            "gen_rate_power": [1000, 2000, 3000]
        })

        df = get_gen_codes_and_names(session, gen_ids)

    assert df.shape == (3, 3)
    assert df.index.tolist() == gen_ids
    assert df.columns.tolist() == ["gen_code", "gen_name", "gen_rate_power"]
    assert df["gen_code"].tolist() == ["code_1", "code_2", "code_3"]
    assert df["gen_name"].tolist() == ["name_1", "name_2", "name_3"]
    assert df["gen_rate_power"].tolist() == [1000, 2000, 3000]


def test_get_client_settings():
    cli_id = 1
    session = UnifiedAlchemyMagicMock()
    with mock.patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = pd.DataFrame({
            "cli_set_name": ["name_1", "name_2", "name_3"],
            "cli_set_value": ["value_1", "value_2", "value_3"]
        })

        df = get_client_settings(session, cli_id)

    assert df.shape == (3, 1)
    assert df.index.tolist() == ["name_1", "name_2", "name_3"]
    assert df["cli_set_value"].tolist() == ["value_1", "value_2", "value_3"]


def test_insert_cli_gen_alerts():
    cli_id = 1
    gen_ids = [1, 2, 3]
    datetime_start = datetime(2021, 1, 1, 0, 0, 0)
    datetime_end = datetime(2021, 1, 2, 0, 0, 0)
    rows_to_insert = [
        {"cli_id": 1, "gen_id": 1, "cli_gen_alert_trigger": datetime(2021, 1, 1, 0, 0, 0)},
        {"cli_id": 1, "gen_id": 2, "cli_gen_alert_trigger": datetime(2021, 1, 1, 0, 0, 0)},
        {"cli_id": 1, "gen_id": 3, "cli_gen_alert_trigger": datetime(2021, 1, 1, 0, 0, 0)}
    ]
    mock_statement = mock.Mock()
    mock_insert = mock.Mock(return_value=mock_statement)
    mock_statement.values = mock.Mock(return_value="statement")
    session = UnifiedAlchemyMagicMock()
    with mock.patch('sqlalchemy.dialects.postgresql.insert', mock_insert):
        with mock.patch("sqlalchemy.orm.Session.execute") as mock_execute:

            mock_execute.return_value = None

            result = insert_cli_gen_alerts(session, cli_id, gen_ids, datetime_start, datetime_end, rows_to_insert)

            assert result == 3
            mock_insert.assert_called_once_with(CliGenAlert)
            session.execute.assert_called_once_with("statement")
            session.commit.assert_called_once()


def test_get_gen_ids_by_data_pro_id():
    data_pro_id = 1
    session = UnifiedAlchemyMagicMock()
    with mock.patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = pd.DataFrame({
            "gen_id": [1, 2, 3],
            "loc_id": [1, 1, 1],
            "cli_id": [1, 1, 1],
            "data_date": [datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0)]
        })

        result = get_gen_ids_by_data_pro_id(session, data_pro_id)

        assert result == (1, 1, [1, 2, 3], datetime(2021, 1, 1, 0, 0, 0), datetime(2021, 1, 1, 0, 0, 0))


def test_get_gen_ids_by_data_pro_id_multi_cli_loc():
    data_pro_id = 1
    session = UnifiedAlchemyMagicMock()
    with mock.patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = pd.DataFrame({
            "gen_id": [1, 2, 3],
            "loc_id": [1, 2, 3],
            "cli_id": [1, 2, 3],
            "data_date": [datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0),
                          datetime(2021, 1, 1, 0, 0, 0)]
        })

        with pytest.raises(ValueError):
            get_gen_ids_by_data_pro_id(session, data_pro_id)


def test_get_location():
    location = Location(loc_id_auto=1, loc_name="name", cli_id=1)

    session = UnifiedAlchemyMagicMock(data=[
        (
            [mock.call.query(Location),
             mock.call.filter(Location.loc_id_auto == location.loc_id_auto and
                              Location.cli_id == location.cli_id)],
            [location]
        )])
    assert get_location(session, location.loc_id_auto, location.cli_id) == location


def test_update_location():
    cli_id = 1
    location = Location(loc_id_auto=1, loc_name="name", cli_id=cli_id)

    mock_statement = mock.Mock()
    mock_update = mock.Mock(return_value=mock_statement)
    mock_statement.values = mock.Mock(return_value="statement")

    session = UnifiedAlchemyMagicMock()

    with mock.patch('sqlalchemy.sql.expression.update', mock_update):
        with mock.patch("sqlalchemy.orm.Session.execute") as mock_execute:

            mock_execute.return_value = None
            capacity = 50
            update_location(session, location, "address", capacity)
            session.commit.assert_called_once()
