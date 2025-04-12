from datetime import datetime
from typing import Dict

import pandas as pd
from db.utils import (get_expected_data_count_per_period, get_gen_data_count,
                      get_period_end, get_sta_data_count)
from sqlalchemy.orm import Session


def _get_data_availability(count_df: pd.DataFrame, datetime_start: datetime, datetime_end: datetime, data_type_names: Dict[int, str], pd_freq: str, data_freq: str) -> pd.DataFrame:

    # Get df with all the group by periods corresponding to the start and end date
    # E.g. if group_by is 'day' and start_date is 2023-01-01 and end_date is 2023-01-10
    # then the periods will be 2023-01-01, 2023-01-02, ..., 2023-01-10
    periods = pd.date_range(datetime_start, datetime_end, freq=pd_freq)
    full_index = pd.MultiIndex.from_product(
        [data_type_names.keys(), periods],
        names=['data_type_id', 'period']
    )
    all_periods = pd.DataFrame(index=full_index).reset_index()
    if all_periods.empty:
        return pd.DataFrame()

    # Merge the actual data with the periods to fill in the missing gaps in the data
    df = all_periods.merge(count_df, on=['data_type_id', 'period'], how='left').fillna(0)

    df['expected_count'] = df.apply(lambda row: get_expected_data_count_per_period(row['period'], datetime_end, pd_freq, data_freq), axis=1)
    df['data_availability_pct'] = df['data_count'] / df['expected_count'] * 100

    df = df.pivot_table(
        values='data_availability_pct',
        index=['period'],
        columns=['data_type_id']
    )
    df.rename(columns=data_type_names, inplace=True)
    df['from'] = df.index
    df['to'] = df.apply(
        lambda x: get_period_end(x['from'], pd_freq, datetime_end), axis=1)

    # The resulting df will look like this:
    # from               power from                 to
    # 2024-07-01 00:00:00  100.0 2024-07-01 00:00:00 2024-07-01 00:59:59
    # 2024-07-01 01:00:00  100.0 2024-07-01 01:00:00 2024-07-01 01:59:59
    # 2024-07-01 02:00:00  100.0 2024-07-01 02:00:00 2024-07-01 02:59:59

    return df


def calculate_data_availability(db: Session, loc_id: int, datetime_start: datetime, datetime_end: datetime, group_by: str, pd_freq: str, data_freq: str) -> pd.DataFrame:

    gen_data_count_df = get_gen_data_count(db, loc_id, datetime_start, datetime_end, [502], group_by)
    gen_data_availability = _get_data_availability(
        gen_data_count_df, datetime_start, datetime_end, {502: 'power'}, pd_freq, data_freq)

    sta_data_count_df = get_sta_data_count(db, loc_id, datetime_start, datetime_end, [503, 505], group_by)
    sta_data_availability = _get_data_availability(sta_data_count_df, datetime_start, datetime_end, {503: 'temperature', 505: 'irradiation'}, pd_freq, data_freq)

    # Merge the data availability for gen and sta by index
    if gen_data_availability.empty or sta_data_availability.empty:
        return pd.DataFrame()
    data_availability = gen_data_availability.merge(sta_data_availability, on=['from', 'to'], how='outer')

    return data_availability
