from datetime import datetime, timedelta
from typing import List, Tuple
import numpy as np
import pandas as pd
from core.solar import Solar
from db.utils import get_co2_emissions_per_kwh
from db.db import session


def _fill_missing_data(df: pd.DataFrame, datetime_start: datetime, datetime_end: datetime) -> pd.DataFrame:
        all_time = pd.DataFrame({'data_date': np.arange(datetime_start, datetime_end, timedelta(minutes=15))}).set_index('data_date')
        df = pd.merge(all_time, df, how='left', left_index=True, right_index=True)
        df.fillna(0, inplace=True)
        return df

def calculate_co2_avoided(cli_id: int, loc_id:int, datetime_start: datetime, datetime_end: datetime, freq: str) -> Tuple[int, int, List[int], datetime, datetime, int]:
    solar = Solar(cli_id, loc_id, None, None, datetime_start, datetime_end, freq)

    solar.fetch_aggregated_by_loc_and_period()
    co2 = get_co2_emissions_per_kwh(session, solar.loc_id, datetime_start, datetime_end)    
    co2 = _fill_missing_data(co2, datetime_start, datetime_end)
    co2 = co2.groupby(pd.Grouper(freq=freq)).sum().fillna(0)
    df = solar.data_aggregated_by_loc_and_period.merge(co2, on='data_date', how='left')
    df['co2_avoided'] = df['power'] * df['co2_per_kwh']

    return df[['co2_avoided', 'from', 'to']]