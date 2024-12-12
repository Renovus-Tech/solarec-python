from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np
import pandas as pd
from core.solar import Solar
from db.db import session
from db.utils import get_client_settings, get_co2_emissions_per_kwh, get_group_period_end_date


def _fill_missing_data(df: pd.DataFrame, datetime_start: datetime, datetime_end: datetime, data_freq_timedelta: timedelta) -> pd.DataFrame:
    all_time = pd.DataFrame({'data_date': np.arange(datetime_start, datetime_end, data_freq_timedelta)}).set_index('data_date')
    df = pd.merge(all_time, df, how='left', left_index=True, right_index=True)
    df.ffill(inplace=True)
    df.fillna(0, inplace=True)
    return df


def calculate_co2_avoided(cli_id: int, loc_id: int, datetime_start: datetime, datetime_end: datetime, freq: str, data_freq: str, data_freq_timedelta: timedelta) -> pd.DataFrame:
    solar = Solar(cli_id, loc_id, None, None, datetime_start, datetime_end, freq, data_freq)

    solar.fetch_aggregated_by_loc_and_period()
    co2 = get_co2_emissions_per_kwh(session, solar.loc_id, datetime_start, datetime_end)
    client_settings = get_client_settings(session, cli_id)

    if 'certSoldPorcentage' in client_settings.index:
        cert_sold_pct = client_settings.loc['certSoldPorcentage']['cli_set_value'] or 0
    else:
        cert_sold_pct = 0

    if 'certPrice' in client_settings.index:
        cert_price = client_settings.loc['certPrice']['cli_set_value'] or 0
    else:
        cert_price = 0

    cert_sold_pct = int(cert_sold_pct) / 100
    cert_price = int(cert_price)

    co2 = _fill_missing_data(co2, datetime_start, datetime_end, data_freq_timedelta)

    df = solar.data[['power', 'from']].merge(co2, on='data_date', how='left')

    df['cert_generated'] = df['power']
    df['co2_avoided'] = df['power'] * df['co2_per_mwh']
    df['cert_generated'] = df['power']
    df['cert_sold'] = df['cert_generated'] * cert_sold_pct
    df['price'] = df['cert_generated'] * cert_price
    df['income'] = df['cert_sold'] * cert_price
    # co2_per_mwh should be the average of the period
    agg = {'power': 'sum', 'co2_avoided': 'sum', 'cert_sold': 'sum', 'cert_generated': 'sum', 'price': 'sum', 'income': 'sum', 'from': 'first', 'co2_per_mwh': 'mean'}

    df = df.groupby(pd.Grouper(freq=freq)).agg(agg).fillna(0)

    df['to'] = df.apply(lambda x: get_group_period_end_date(x, solar.freq, solar.datetime_end), axis=1)
    return df[['co2_avoided', 'cert_sold', 'cert_generated', 'co2_per_mwh', 'price', 'income', 'from', 'to']]
