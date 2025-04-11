from datetime import datetime, timedelta
from typing import List, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
from core.solar import Solar
from db.utils import get_client_settings, get_co2_emissions_tons_per_Mwh, get_gen_ids_by_loc_id, get_group_period_end_date, get_sta_id_by_loc_id


def calculate_data_availability(db: Session, cli_id: int, loc_id: int, datetime_start: datetime, datetime_end: datetime, freq: str) -> pd.DataFrame:
    gen_ids = gen_ids if gen_ids else [
        int(x) for x in get_gen_ids_by_loc_id(db, loc_id)['gen_id_auto'].values]

    station = get_sta_id_by_loc_id(db, loc_id)
    if station.empty:
        raise HTTPException(status_code=400, detail=f'No station found for location {loc_id}')
    sta_id = int(station['sta_id_auto'][0])

    gen_df = get_gens_data_availability(db, gen_ids, datetime_start, datetime_end, {502: 'power'}, freq)
    sta_df = get_sta_data_availability(db, sta_id, datetime_start, datetime_end, {503: 'temperature', 505: 'irradiation'}, freq)
