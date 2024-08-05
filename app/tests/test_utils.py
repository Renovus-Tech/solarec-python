from datetime import datetime
from unittest import mock

from db.models import Location
from db.utils import get_loc_output_capacity, get_period_end
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
