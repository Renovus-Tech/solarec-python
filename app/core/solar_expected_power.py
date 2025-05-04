from datetime import datetime

import pandas as pd
from db.utils import get_loc_output_capacity, get_period_end, get_sta_data
from sqlalchemy.orm import Session

PERFORMANCE_RATIO = 0.8


def get_expected_power(db: Session, cli_id: int, loc_id: int, datetime_start: datetime, datetime_end: datetime, pd_freq: str, data_freq: str) -> pd.DataFrame:

    loc_capacity = get_loc_output_capacity(db, loc_id)
    df = get_sta_data(db, cli_id, loc_id, datetime_start, datetime_end, data_freq, {505: 'irradiation'})

    if df.empty:
        return pd.DataFrame()
    if pd_freq:
        df = df.reset_index().set_index('data_date').groupby([pd.Grouper(freq=pd_freq)]).agg({'irradiation': 'sum'})

    df['expected_power'] = df.apply(lambda x: x['irradiation'] * loc_capacity * PERFORMANCE_RATIO / 1000, axis=1)

    df['from'] = df.index
    df['to'] = df.apply(
        lambda x: get_period_end(x['from'], pd_freq, datetime_end), axis=1)
    return df
