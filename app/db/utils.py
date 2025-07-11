import datetime
import time
from typing import Dict, List, Optional, Tuple

import pandas as pd
import sqlalchemy.dialects.postgresql as pq
from dateutil.relativedelta import SU, relativedelta
from db.models import (CliGenAlert, CliSetting, CtrData, GenData, Generator,
                       Location, StaData, Station)
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import extract


def get_group_period_end_date(rows, freq, datetime_end):
    return get_period_end(rows['from'], freq, datetime_end)


def get_period_end(datetime_start, freq, end_date):

    period_end = None
    if freq is None:
        return end_date

    if freq == "1H":
        period_end = datetime_start + relativedelta(hours=1, seconds=-1)

    if freq == "1D":
        period_end = datetime_start + \
            relativedelta(days=1, hour=0, minute=0, seconds=-1)

    if freq == "1W":
        period_end = datetime_start + \
            relativedelta(weekday=SU, days=1, hour=23, minute=59, second=59)

    if freq == "1M" or freq == "1MS":
        period_end = datetime_start + \
            relativedelta(months=1, day=1, days=-1,
                          hour=23, minute=59, second=59)

    if freq == "1Y" or freq == "1YS":
        period_end = datetime.datetime(datetime_start.year, 12, 31, 23, 59, 59)

    if freq == "15T":
        period_end = datetime_start + relativedelta(minutes=15, seconds=-1)

    if period_end is None or period_end > end_date:
        return datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

    return period_end


def group_by_to_pd_frequency(group_by):

    if group_by == "hour":
        return "1H"

    if group_by == "day":
        return "1D"

    if group_by == "week":
        return "1W"

    if group_by == "month":
        return "1MS"

    if group_by == "year":
        return "1YS"


def data_freq_to_pd_frequency(frqNumber: int, frqUnit: str) -> str:

    if frqUnit == 'm':
        return f"{frqNumber}T"

    if frqUnit == 'h':
        return f"{frqNumber}H"

    if frqUnit == 'd':
        return f"{frqNumber}D"

    if frqUnit == 'w':
        return f"{frqNumber}W"

    if frqUnit == 't':
        return f"{frqNumber}MS"

    if frqUnit == 'y':
        return f"{frqNumber}YS"

    return None


def pandas_frequency_to_timedelta(freq):
    freq_map = {
        'D': datetime.timedelta(days=1),
        'H': datetime.timedelta(hours=1),
        'T': datetime.timedelta(minutes=1),
        'W': datetime.timedelta(weeks=1),
        'M': relativedelta(months=1),
        'MS': relativedelta(months=1),
        'Y': relativedelta(years=1)
    }

    def convert_to_timedelta(freq_timedelta):
        if isinstance(freq_timedelta, relativedelta):
            # Asume 30 days per month and 365 days per year
            days = freq_timedelta.years * 365 + freq_timedelta.months * 30
            return datetime.timedelta(days=days)
        return freq_timedelta

    multiplier = 1
    for key in freq_map:
        if freq.endswith(key):
            if freq[:-len(key)].isdigit():
                multiplier = int(freq[:-len(key)])
            return convert_to_timedelta(freq_map[key] * multiplier)

    raise ValueError(f"Frequency not supported: {freq}")


def remove_microseconds(row):
    ms = row.microsecond
    if ms > 500000:
        return row.replace(microsecond=0) + datetime.timedelta(seconds=1)
    else:
        return row.replace(microsecond=0)


def adjust_data_date_by_freq(row, freq):
    if freq in ['1MS', '1Y']:
        return row.replace(hour=0, minute=0, second=0, microsecond=0)
    return row


def get_gen_datas_grouped(db: Session, cli_id: int, gen_ids: list, datetime_start, datetime_end, freq: str, data_type_names: Dict[int, str]) -> pd.DataFrame:
    """
    Get generator data for multiple data types and multiple generators.
    """
    t0 = time.time()
    df = pd.read_sql(
        db.query(GenData.gen_id, GenData.data_date,
                 GenData.data_value, GenData.data_type_id)
        .filter(GenData.gen_id.in_(gen_ids))
        .filter(GenData.data_type_id.in_(data_type_names.keys()))
        .filter(GenData.data_date < datetime_end)
        .filter(GenData.data_date >= datetime_start)
        .statement,
        db.bind)

    if not df.empty:
        df["data_date"] = df["data_date"].apply(
            lambda row: remove_microseconds(row))
        df['data_date'] = df['data_date'] - \
            pd.to_timedelta(df['data_date'].dt.second, unit='s')
        df['data_date'] = df['data_date'].apply(
            lambda row: adjust_data_date_by_freq(row, freq))

    df = pd.pivot_table(df, values='data_value', index=[
                        'gen_id', 'data_date'], columns='data_type_id')
    df.rename(columns=data_type_names, inplace=True)
    for column in [x for x in data_type_names.values() if x not in df.columns]:
        df[column] = None
    t1 = time.time()
    print(
        f"Function get_gen_datas for {len(gen_ids)} generators and {len(data_type_names.keys())} data types took {t1 - t0:.2f} seconds.")
    return df


def get_sta_datas_grouped(db: Session, cli_id: int, sta_id: int, datetime_start, datetime_end, data_freq: str, data_type_names: Dict[int, str]) -> pd.DataFrame:
    """
    Get data for multiple data types grouped by date_time.
    """
    t0 = time.time()
    df = pd.read_sql(
        db.query(
            StaData.sta_id, StaData.data_date, StaData.data_value, StaData.data_type_id
        )
        .filter(StaData.cli_id == cli_id)
        .filter(StaData.sta_id == sta_id)
        .filter(StaData.data_type_id.in_(data_type_names.keys()))
        .filter(StaData.data_date < datetime_end)
        .filter(StaData.data_date >= datetime_start)
        .statement,
        db.bind)

    if not df.empty:
        df["data_date"] = df["data_date"].apply(
            lambda row: remove_microseconds(row))
        df['data_date'] = df['data_date'] - pd.to_timedelta(df['data_date'].dt.second, unit='s')
        df['data_date'] = df['data_date'].apply(
            lambda row: adjust_data_date_by_freq(row, data_freq))

    result = pd.DataFrame()
    result['data_date'] = df['data_date']
    result['sta_id'] = df['sta_id']
    for data_type_id, data_name in data_type_names.items():
        result[data_name] = df[df['data_type_id'] == data_type_id]['data_value']
    t1 = time.time()
    print(f"Function get_sta_datas for1 stations and {len(data_type_names.keys())} data types took {t1 - t0:.2f} seconds.")
    result = result.groupby(['data_date', 'sta_id']).sum()

    for column in [x for x in data_type_names.values() if x not in result.columns]:
        result[column] = None

    return result


def get_gen_datas(
    db: Session,
    gen_ids: list,
    data_type_ids: int,
    datetime_start,
    datetime_end,
    data_name: str = "data_value",


):
    """
    Get generator data for multiple data types and multiple generators.
    """
    t0 = time.time()
    df = pd.read_sql(
        db.query(
            GenData.gen_id, GenData.data_date, GenData.data_value, GenData.data_type_id
        )
        .filter(GenData.gen_id.in_(gen_ids))
        .filter(GenData.data_type_id.in_(data_type_ids))
        .filter(GenData.data_date < datetime_end)
        .filter(GenData.data_date >= datetime_start)
        .statement,
        db.bind,
    ).rename(columns={"data_value": data_name})
    df["data_date"] = df["data_date"].apply(
        lambda row: remove_microseconds(row))
    t1 = time.time()
    print(
        f"Function get_gen_datas for {len(gen_ids)} generators and {len(data_type_ids)} data types took {t1 - t0:.2f} seconds."
    )
    return df


def get_sta_datas(
    db: Session,
    sta_ids: list,
    data_type_ids: list,
    datetime_start,
    datetime_end,
    data_name: str = "data_value",
):
    """
    Get data for multiple data types and multiple stations.
    """
    t0 = time.time()
    df = pd.read_sql(
        db.query(
            StaData.sta_id, StaData.data_date, StaData.data_value, StaData.data_type_id
        )
        .filter(StaData.sta_id.in_(sta_ids))
        .filter(StaData.data_type_id.in_(data_type_ids))
        .filter(StaData.data_date < datetime_end)
        .filter(StaData.data_date >= datetime_start)
        .statement,
        db.bind,
    ).rename(columns={"data_value": data_name})
    df["data_date"] = df["data_date"].apply(
        lambda row: remove_microseconds(row))
    t1 = time.time()
    print(
        f"Function get_sta_datas for {len(sta_ids)} stations and {len(data_type_ids)} data types took {t1 - t0:.2f} seconds."
    )
    return df


def get_gen_ids_by_loc_id(db: Session, loc_id: int):
    df = pd.read_sql(db.query(Generator.gen_id_auto)
                     .filter(Generator.loc_id == loc_id)
                     .statement,
                     db.bind)
    return df


def get_gen_id_by_loc_id(db: Session, loc_id: int) -> int:
    return int(get_gen_ids_by_loc_id(db, loc_id)['gen_id_auto'].values[0])


def get_sta_id_by_loc_id(db: Session, loc_id: int):
    df = pd.read_sql(db.query(Station.sta_id_auto)
                     .filter(Station.loc_id == loc_id)
                     .statement,
                     db.bind)
    return df


def get_gen_codes_and_names(db: Session, gen_ids: List[int]):
    df = pd.read_sql(
        db.query(Generator.gen_id_auto, Generator.gen_code,
                 Generator.gen_name, Generator.gen_rate_power)
        .filter(Generator.gen_id_auto.in_(gen_ids))
        .statement, db.bind)
    return df.set_index(df['gen_id_auto']).drop('gen_id_auto', axis=1)


def get_loc_output_capacity(db: Session, locId: int):
    capacity = (
        db.query(Location.loc_output_capacity)
        .filter(Location.loc_id_auto == locId)
        .first()
    )
    if capacity is None:
        raise ValueError(f"Location capacity not found for locId {locId}")
    return capacity[0]


def get_client_settings(db: Session, cli_id: int):
    df = pd.read_sql(
        db.query(CliSetting.cli_set_name, CliSetting.cli_set_value)
        .filter(CliSetting.cli_id == cli_id)
        .statement, db.bind
    )
    return df.set_index('cli_set_name', drop=True)


def insert_cli_gen_alerts(db: Session, cli_id: int, gen_ids: List[int], datetime_start: datetime.datetime, datetime_end: datetime.datetime, rows_to_insert: List[Dict]) -> int:

    db.query(CliGenAlert).filter(
        CliGenAlert.cli_id == cli_id,
        CliGenAlert.gen_id.in_(gen_ids),
        CliGenAlert.cli_gen_alert_trigger >= datetime_start,
        CliGenAlert.cli_gen_alert_trigger < datetime_end
    ).delete()

    if len(rows_to_insert) > 0:
        statement = pq.insert(CliGenAlert).values(rows_to_insert)
        db.execute(statement)
        db.commit()

    return len(rows_to_insert)


def get_gen_ids_by_data_pro_id(db: Session, data_pro_id: int) -> Tuple[int, int, List[int], datetime.datetime, datetime.datetime]:

    df = pd.read_sql(db.query(GenData.gen_id, Generator.loc_id, Generator.cli_id, GenData.data_date)
                     .join(Generator, Generator.gen_id_auto == GenData.gen_id)
                     .filter(GenData.data_pro_id == data_pro_id)
                     .statement, db.bind)

    if (df.empty):
        return None, None, None, None, None

    cli_id = list(set(df['cli_id']))
    loc_id = list(set(df['loc_id']))
    gen_ids = list(set(df['gen_id']))
    min_date = min(df['data_date'])
    max_date = max(df['data_date'])

    if len(cli_id) > 1 or len(loc_id) > 1:
        raise ValueError('data_pro_id does not correspond to a single client or location')
    return cli_id[0], loc_id[0], gen_ids, min_date, max_date


def get_co2_emissions_tons_per_Mwh(db: Session, loc_id: int, datetime_start: datetime.datetime, datetime_end: datetime.datetime, freq: str) -> pd.DataFrame:
    query = (
        db.query(CtrData.data_value, extract('year', CtrData.data_date).label('year'))
        .join(Location, Location.ctr_id == CtrData.ctr_id)
        .filter(Location.loc_id_auto == loc_id)
        .filter(CtrData.data_type_id == 901)
        .order_by(CtrData.data_date.desc())
    )
    df = pd.read_sql(query.statement, db.bind)
    df['year'] = df['year'].astype(int)
    all_time = pd.date_range(datetime_start, datetime_end, freq=freq)

    if df.empty:
        result = pd.DataFrame({'data_time': all_time, 'data_value': 0})
    else:
        result = pd.DataFrame()

        for time in all_time:
            # For each year, the value is the average of the last available 3 years from df
            year = int(time.year)
            last_3_years = df[df['year'] <= year].tail(3)
            value = last_3_years['data_value'].mean() / 1000 if not last_3_years.empty else 0
            result = pd.concat([result, pd.DataFrame({
                'data_time': [time],
                'data_value': [value]
            })], ignore_index=True)

    return result.set_index('data_time')


def get_location(db: Session, loc_id: int, cli_id: int) -> Location:
    return db.query(Location).filter(Location.loc_id_auto == loc_id and
                                     Location.cli_id == cli_id).first()


def update_location(db: Session, location: Location, address: Optional[str], capacity: Optional[int]):
    if address:
        location.loc_address = address
    if capacity:
        location.loc_output_total_capacity = capacity
    db.commit()


def get_gen_data(db: Session, cli_id, gen_id, start_date, end_date) -> pd.DataFrame:
    df = pd.read_sql(db.query(GenData.data_date, GenData.data_value, GenData.data_pro_id)
                     .filter(GenData.cli_id == cli_id,
                             GenData.gen_id == gen_id,
                             GenData.data_date >= start_date,
                             GenData.data_date < end_date,
                             GenData.data_type_id == 502)
                     .statement, db.bind)
    df.columns = ['data_date', 'Generated Power', 'data_pro_id']
    df["data_date"] = df["data_date"].apply(
        lambda row: remove_microseconds(row))
    df.set_index('data_date', inplace=True)
    return df


def get_sta_data(db: Session, cli_id, loc_id, start_date, end_date, data_freq='15T', data_type_names={503: 'Temperature', 507: 'Precipitation Total', 506: 'Cloud Cover Total', 505: 'Shortwave Radiation'}) -> pd.DataFrame:
    sta_id_query = db.query(Station.sta_id_auto).filter(Station.cli_id == cli_id, Station.loc_id == loc_id).first()
    if sta_id_query is None or len(sta_id_query) == 0:
        raise ValueError(f"No station found for cli_id {cli_id} and loc_id {loc_id}")
    sta_id = sta_id_query[0]
    df = pd.read_sql(db.query(StaData.data_date, StaData.data_type_id, StaData.data_value)
                     .filter(StaData.cli_id == cli_id,
                             StaData.sta_id == sta_id,
                             StaData.data_date >= start_date,
                             StaData.data_date < end_date,
                             StaData.data_type_id.in_(data_type_names.keys()))
                     .statement, db.bind)
    if not df.empty:
        df["data_date"] = df["data_date"].apply(
            lambda row: remove_microseconds(row))
        df['data_date'] = df['data_date'] - \
            pd.to_timedelta(df['data_date'].dt.second, unit='s')
        df['data_date'] = df['data_date'].apply(
            lambda row: adjust_data_date_by_freq(row, data_freq))

    df = pd.pivot_table(df, values='data_value', index=['data_date'], columns='data_type_id')
    df.rename(columns=data_type_names, inplace=True)

    return df


def insert_or_update_predictions(db: Session, cli_id: int, gen_id: int, predictions: List[Tuple[datetime.datetime, float, int]]):
    rows_to_insert = []
    for prediction in predictions:
        rows_to_insert.append({
            'cli_id': cli_id,
            'gen_id': gen_id,
            'data_date': prediction[0],
            'data_type_id': 508,
            'data_pro_id': prediction[2],
            'data_value': prediction[1],
            'data_date_added': datetime.datetime.now()
        })

    insert_stmt = pq.insert(GenData).values(rows_to_insert)

    update_stmt = insert_stmt.on_conflict_do_update(
        index_elements=['cli_id', 'gen_id', 'data_date', 'data_type_id'],  # Primary Key
        set_={
            'data_value': insert_stmt.excluded.data_value,
            'data_pro_id': insert_stmt.excluded.data_pro_id,
            'data_date_added': datetime.datetime.now()
        }
    )

    db.execute(update_stmt)
    db.commit()


def get_gen_data_count(db: Session, loc_id: int, datetime_start, datetime_end, data_types: List[int], group_by: str) -> pd.DataFrame:
    valid_frequencies = {'hour', 'day', 'week', 'month', 'year'}
    if group_by not in valid_frequencies:
        raise ValueError(f"Invalid group_by value. Must be one of {valid_frequencies}")

    trunc_function = func.date_trunc(group_by, GenData.data_date).label('period')
    query = (
        db.query(
            GenData.data_type_id,
            trunc_function,
            func.count().label('data_count')
        )
        .filter(
            Generator.loc_id == loc_id,
            GenData.data_type_id.in_(data_types),
            GenData.data_date >= datetime_start,
            GenData.data_date < (datetime_end + datetime.timedelta(seconds=1))
        )
        .join(
            Generator,
            Generator.gen_id_auto == GenData.gen_id)
        .group_by(
            GenData.data_type_id,
            trunc_function
        )
    )

    return pd.read_sql(query.statement, db.bind)


def get_sta_data_count(db: Session, loc_id: int, datetime_start, datetime_end, data_types: List[int], group_by: str) -> pd.DataFrame:
    valid_frequencies = {'hour', 'day', 'week', 'month', 'year'}
    if group_by not in valid_frequencies:
        raise ValueError(f"Invalid group_by value. Must be one of {valid_frequencies}")

    trunc_function = func.date_trunc(group_by, StaData.data_date).label('period')
    query = (
        db.query(
            StaData.data_type_id,
            trunc_function,
            func.count().label('data_count')
        )
        .filter(
            Station.loc_id == loc_id,
            StaData.data_type_id.in_(data_types),
            StaData.data_date >= datetime_start,
            StaData.data_date < (datetime_end + datetime.timedelta(seconds=1))
        )
        .join(
            Station,
            Station.sta_id_auto == StaData.sta_id)
        .group_by(
            StaData.data_type_id,
            trunc_function
        )
    )

    return pd.read_sql(query.statement, db.bind)


def get_expected_data_count_per_period(period_start: datetime.datetime, datetime_end: datetime.datetime,  pd_freq: str, data_freq: str) -> int:
    """
    Calculate the expected data count per period based on the group by frequency and the data frequency.
    # E.g. if pd_freq is '1H' and data_freq is '15T', then the expected count is 4
    """
    period_end = get_period_end(period_start, pd_freq, datetime_end) + datetime.timedelta(seconds=1)
    period_seconds = int((period_end - period_start).total_seconds())

    if data_freq == '1M' or data_freq == '1MS':
        data_freq_seconds = 30 * 24 * 60 * 60
    elif data_freq == '1YS' or data_freq == '1Y':
        data_freq_seconds = 365 * 24 * 60 * 60
    else:
        data_freq_seconds = int(pd.to_timedelta(data_freq).total_seconds())
    return int(period_seconds / data_freq_seconds)


def insert_irradiation_per_month(db: Session, start_date: datetime.datetime, end_date: datetime.datetime):
    # - Toma la suma de la irradiación mensual de sta_data para sta_id=51, data_type_id=505, cli_id=83.
    df = pd.read_sql(db.query(StaData.data_date, StaData.data_value)
                     .filter(StaData.cli_id == 83,
                             StaData.sta_id == 51,
                             StaData.data_type_id == 505,
                             StaData.data_date >= start_date,
                             StaData.data_date < end_date)
                     .statement, db.bind)
    df["data_date"] = df["data_date"].apply(
        lambda row: remove_microseconds(row))
    df = df.groupby(pd.Grouper(key='data_date', freq='M')).sum().reset_index()
    df['data_date'] = df['data_date'].apply(
        lambda row: row.replace(hour=0, minute=0, second=0, microsecond=0))
    df['data_value'] = df['data_value'].astype(float)

    # Guarda esa suma, como un dato único por mes para sta_id=52, data_type_id=505, cli_id=84, data_pro_id=5030.
    rows_to_insert = []
    for index, row in df.iterrows():
        rows_to_insert.append({
            'cli_id': 84,
            'sta_id': 52,
            'data_date': start_date,
            'data_type_id': 505,
            'data_pro_id': 5030,
            'data_value': row['data_value'],
            'data_date_added': datetime.datetime.now()
        })
    if rows_to_insert:
        insert_stmt = pq.insert(StaData).values(rows_to_insert)
        db.execute(insert_stmt)
        db.commit()


def insert_production_per_month(db: Session, start_date: datetime.datetime, end_date: datetime.datetime):
    # - Toma la irradiación mensual de sta_data, y calcula la producción y la inserta en gen_data para gen_id=43, cli_id=84 haciendo:
    #       produccion_kwh = irradiación * capacidad_kw * 0.8
    #       la capacidad_kw esta en location.loc_output_total_capacity para loc_id=55
    loc_id = 55
    gen_id = 43
    capacity_kw = get_loc_output_capacity(db, loc_id)
    df = pd.read_sql(db.query(StaData.data_date, StaData.data_value)
                     .filter(StaData.cli_id == 84,
                             StaData.sta_id == 52,
                             StaData.data_type_id == 505,
                             StaData.data_date >= start_date,
                             StaData.data_date < end_date)
                     .statement, db.bind)
    df = df.groupby(pd.Grouper(key='data_date', freq='M')).sum().reset_index()
    df["data_date"] = start_date
    df['data_value'] = df['data_value'].astype(float)
    df['data_value'] = round(df['data_value'] * capacity_kw * 0.8, 0)
    df['data_type_id'] = 502
    df['data_pro_id'] = 5030
    df['cli_id'] = 84
    df['gen_id'] = gen_id
    df['data_date_added'] = datetime.datetime.now()
    rows_to_insert = df.to_dict('records')
    if rows_to_insert:
        insert_stmt = pq.insert(GenData).values(rows_to_insert)
        db.execute(insert_stmt)
        db.commit()


def get_date_intervals_without_data(db: Session, start_date: datetime.datetime, end_date: datetime.datetime) -> List[Tuple[datetime.datetime, datetime.datetime]]:
    #     """ Check sta_data and gen_data for months without data.
    #     Returns a list of tuples with start and end date of the intervals without data.
    #     """
    date_intervals = []
    start_date = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    end_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)

    cli_id = 84
    sta_id = 52
    sta_data_df = pd.read_sql(
        db.query(StaData.data_date)
        .filter(StaData.cli_id == cli_id)
        .filter(StaData.sta_id == sta_id)
        .filter(StaData.data_type_id == 505)  # Shortwave Radiation
        .filter(StaData.data_date >= start_date)
        .filter(StaData.data_date <= end_date)
        .statement,
        db.bind
    )

    sta_data_df_by_month = sta_data_df.groupby(sta_data_df['data_date'].dt.to_period('M')).size().reset_index(name='count')
    all_months_in_interval = pd.date_range(start=start_date, end=end_date, freq='MS').to_period('M')
    missing_months = all_months_in_interval[~all_months_in_interval.isin(sta_data_df_by_month['data_date'])]
    for month in missing_months:
        start = month.start_time
        end = month.end_time
        date_intervals.append((start, end))

    return date_intervals
