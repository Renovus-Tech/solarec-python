import datetime
import time
from typing import Dict, List, Tuple

import pandas as pd
import sqlalchemy.dialects.postgresql as pq
from dateutil.relativedelta import SU, relativedelta
from db.models import (CliGenAlert, CliSetting, CtrData, GenData, Generator,
                       Location, StaData, Station)


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

    if freq == "1M":
        period_end = datetime_start + \
            relativedelta(months=1, day=1, days=-1,
                          hour=23, minute=59, second=59)

    if freq == "1Y":
        period_end = datetime.datetime(datetime_start.year, 12, 31, 23, 59, 59)

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
        return "1M"

    if group_by == "year":
        return "1Y"


def remove_microseconds(row):
    ms = row.microsecond
    if ms > 500000:
        return row.replace(microsecond=0) + datetime.timedelta(seconds=1)
    else:
        return row.replace(microsecond=0)


def get_gen_datas_grouped(session, cli_id: int, gen_ids: list, datetime_start, datetime_end, data_type_names: Dict[int, str]) -> pd.DataFrame:
    """
    Get generator data for multiple data types and multiple generators.
    """
    t0 = time.time()
    df = pd.read_sql(
        session.query(GenData.gen_id, GenData.data_date,
                      GenData.data_value, GenData.data_type_id)
        .filter(GenData.gen_id.in_(gen_ids))
        .filter(GenData.data_type_id.in_(data_type_names.keys()))
        .filter(GenData.data_date < datetime_end)
        .filter(GenData.data_date >= datetime_start)
        .statement,
        session.bind)

    df["data_date"] = df["data_date"].apply(
        lambda row: remove_microseconds(row))
    if not df.empty:
        df['data_date'] = df['data_date'] - \
            pd.to_timedelta(df['data_date'].dt.second, unit='s')
    df = pd.pivot_table(df, values='data_value', index=[
                        'gen_id', 'data_date'], columns='data_type_id')
    df.rename(columns=data_type_names, inplace=True)
    for column in [x for x in data_type_names.values() if x not in df.columns]:
        df[column] = None
    t1 = time.time()
    print(
        f"Function get_gen_datas for {len(gen_ids)} generators and {len(data_type_names.keys())} data types took {t1 - t0:.2f} seconds.")
    return df


def get_sta_datas_grouped(session, cli_id: int, sta_id: int, datetime_start, datetime_end, data_type_names: Dict[int, str]) -> pd.DataFrame:
    """
    Get data for multiple data types grouped by date_time.
    """
    t0 = time.time()
    df = pd.read_sql(
        session.query(
            StaData.sta_id, StaData.data_date, StaData.data_value, StaData.data_type_id
        )
        .filter(StaData.cli_id == cli_id)
        .filter(StaData.sta_id == sta_id)
        .filter(StaData.data_type_id.in_(data_type_names.keys()))
        .filter(StaData.data_date < datetime_end)
        .filter(StaData.data_date >= datetime_start)
        .statement,
        session.bind)
    df["data_date"] = df["data_date"].apply(
        lambda row: remove_microseconds(row))
    if not df.empty:
        df['data_date'] = df['data_date'] - pd.to_timedelta(df['data_date'].dt.second, unit='s')
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
    session,
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
        session.query(
            GenData.gen_id, GenData.data_date, GenData.data_value, GenData.data_type_id
        )
        .filter(GenData.gen_id.in_(gen_ids))
        .filter(GenData.data_type_id.in_(data_type_ids))
        .filter(GenData.data_date < datetime_end)
        .filter(GenData.data_date >= datetime_start)
        .statement,
        session.bind,
    ).rename(columns={"data_value": data_name})
    df["data_date"] = df["data_date"].apply(
        lambda row: remove_microseconds(row))
    t1 = time.time()
    print(
        f"Function get_gen_datas for {len(gen_ids)} generators and {len(data_type_ids)} data types took {t1 - t0:.2f} seconds."
    )
    return df


def get_sta_datas(
    session,
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
        session.query(
            StaData.sta_id, StaData.data_date, StaData.data_value, StaData.data_type_id
        )
        .filter(StaData.sta_id.in_(sta_ids))
        .filter(StaData.data_type_id.in_(data_type_ids))
        .filter(StaData.data_date < datetime_end)
        .filter(StaData.data_date >= datetime_start)
        .statement,
        session.bind,
    ).rename(columns={"data_value": data_name})
    df["data_date"] = df["data_date"].apply(
        lambda row: remove_microseconds(row))
    t1 = time.time()
    print(
        f"Function get_sta_datas for {len(sta_ids)} stations and {len(data_type_ids)} data types took {t1 - t0:.2f} seconds."
    )
    return df


def get_gen_ids_by_loc_id(session, loc_id: int):
    df = pd.read_sql(session.query(Generator.gen_id_auto)
                     .filter(Generator.loc_id == loc_id)
                     .statement,
                     session.bind)
    return df


def get_sta_id_by_loc_id(session, loc_id: int):
    df = pd.read_sql(session.query(Station.sta_id_auto)
                     .filter(Station.loc_id == loc_id)
                     .statement,
                     session.bind)
    return df


def get_gen_codes_and_names(session, gen_ids: List[int]):
    df = pd.read_sql(
        session.query(Generator.gen_id_auto, Generator.gen_code,
                      Generator.gen_name, Generator.gen_rate_power)
        .filter(Generator.gen_id_auto.in_(gen_ids))
        .statement, session.bind)
    return df.set_index(df['gen_id_auto']).drop('gen_id_auto', axis=1)


def get_loc_output_capacity(session, locId: int):
    return (
        session.query(Location.loc_output_capacity)
        .filter(Location.loc_id_auto == locId)
        .first()[0]
    )


def get_client_settings(session, cli_id: int):
    df = pd.read_sql(
        session.query(CliSetting.cli_set_name, CliSetting.cli_set_value)
        .filter(CliSetting.cli_id == cli_id)
        .statement, session.bind
    )
    return df.set_index('cli_set_name', drop=True)


def insert_cli_gen_alerts(session, cli_id: int, gen_ids: List[int], datetime_start: datetime.datetime, datetime_end: datetime.datetime, rows_to_insert: List[Dict]) -> int:

    session.query(CliGenAlert).filter(
        CliGenAlert.cli_id == cli_id,
        CliGenAlert.gen_id.in_(gen_ids),
        CliGenAlert.cli_gen_alert_trigger >= datetime_start,
        CliGenAlert.cli_gen_alert_trigger < datetime_end
    ).delete()

    if len(rows_to_insert) > 0:
        statement = pq.insert(CliGenAlert).values(rows_to_insert)
        session.execute(statement)
        session.commit()

    return len(rows_to_insert)


def get_gen_ids_by_data_pro_id(session, data_pro_id: int) -> Tuple[int, int, List[int], datetime.datetime, datetime.datetime]:

    df = pd.read_sql(session.query(GenData.gen_id, Generator.loc_id, Generator.cli_id, GenData.data_date)
                     .join(Generator, Generator.gen_id_auto == GenData.gen_id)
                     .filter(GenData.data_pro_id == data_pro_id)
                     .statement, session.bind)

    cli_id = list(set(df['cli_id']))
    loc_id = list(set(df['loc_id']))
    gen_ids = list(set(df['gen_id']))
    min_date = min(df['data_date'])
    max_date = max(df['data_date'])

    if len(cli_id) > 1 or len(loc_id) > 1:
        raise ValueError('data_pro_id does not correspond to a single client or location')
    return cli_id[0], loc_id[0], gen_ids, min_date, max_date


def get_co2_emissions_per_kwh(session, loc_id: int, datetime_start: datetime.datetime, datetime_end: datetime.datetime) -> pd.DataFrame:
    df = pd.read_sql(
        session.query(CtrData.data_date, CtrData.data_value)
        .join(Location, Location.ctr_id == CtrData.ctr_id)
        .filter(Location.loc_id_auto == loc_id)
        .filter(CtrData.data_type_id == 901)
        .filter(CtrData.data_date < datetime_end)
        .filter(CtrData.data_date >= datetime_start)
        .statement, session.bind)
    df["data_date"] = df["data_date"].apply(
        lambda row: remove_microseconds(row))

    df.rename(columns={"data_value": "co2_per_mwh"}, inplace=True)
    return df.set_index('data_date')


def get_location(session, loc_id: int, cli_id: int) -> Location:
    return session.query(Location).filter(Location.loc_id_auto == loc_id and
                                          Location.cli_id == cli_id).first()
