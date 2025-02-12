from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np
import pandas as pd
from core.solar import Solar
from db.db import session
from db.utils import get_client_settings, get_co2_emissions_tons_per_Mwh, get_group_period_end_date


def calculate_co2_avoided(cli_id: int, loc_id: int, datetime_start: datetime, datetime_end: datetime, freq: str, data_freq: str) -> pd.DataFrame:
    solar = Solar(cli_id, loc_id, None, None, datetime_start, datetime_end, freq, data_freq)
    solar.fetch_aggregated_by_loc_and_period()

    co2_per_mwh = get_co2_emissions_tons_per_Mwh(session, solar.loc_id, datetime_start)
    client_settings = get_client_settings(session, cli_id)

    cert_sold_pct = int(client_settings.loc['certSoldPorcentage']['cli_set_value']) / 100 if 'certSoldPorcentage' in client_settings.index else 0
    cert_price = int(client_settings.loc['certPrice']['cli_set_value']) if 'certPrice' in client_settings.index else 0

    df = solar.data_aggregated_by_loc_and_period[['power', 'from']]

    df['co2_per_mwh'] = co2_per_mwh
    df['cert_generated'] = df['power']
    df['co2_avoided'] = df['power'] * df['co2_per_mwh']
    df['cert_sold'] = df['cert_generated'] * cert_sold_pct
    df['price'] = df['cert_generated'] * cert_price
    df['income'] = df['cert_sold'] * cert_price

    agg = {
        'power': 'sum',
        'co2_avoided': 'sum',
        'cert_sold': 'sum',
        'cert_generated': 'sum',
        'price': 'sum',
        'income': 'sum',
        'from': 'first',
        'co2_per_mwh': 'mean'
    }

    if freq is not None:
        df = df.groupby(pd.Grouper(freq=freq)).agg(agg)

    df.fillna(0, inplace=True)
    df['to'] = df.apply(lambda x: get_group_period_end_date(x, solar.freq, solar.datetime_end), axis=1)

    return df[['co2_avoided', 'cert_sold', 'cert_generated', 'co2_per_mwh', 'price', 'income', 'from', 'to']]
