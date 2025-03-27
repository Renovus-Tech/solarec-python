from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException
import numpy as np
import pandas as pd
from db.utils import get_gen_codes_and_names, get_gen_datas_grouped, get_gen_ids_by_loc_id, get_period_end, get_sta_datas_grouped, get_sta_id_by_loc_id, get_loc_output_capacity, insert_cli_gen_alerts
from sqlalchemy.orm import Session


class Solar():
    def __init__(self, db: Session, cli_id: int, loc_id: int, gen_ids: List[int], sta_id: int,  datetime_start: datetime, datetime_end: datetime, freq: str, data_freq: Optional[str] = '15T'):
        self.loc_id = loc_id
        self.gen_ids = gen_ids if gen_ids else [
            int(x) for x in get_gen_ids_by_loc_id(db, loc_id)['gen_id_auto'].values]
        if sta_id:
            self.sta_id = sta_id
        else:
            station = get_sta_id_by_loc_id(db, loc_id)
            if station.empty:
                raise HTTPException(status_code=400, detail=f'No station found for location {loc_id}')
            self.sta_id = int(station['sta_id_auto'][0])
        self.datetime_start = datetime_start
        self.datetime_end = datetime_end
        self.data: pd.DataFrame
        self.cli_id = cli_id
        self.freq = freq
        self.data_freq = data_freq

        loc_total_capacity = get_loc_output_capacity(db, self.loc_id)
        self.loc_total_capacity = loc_total_capacity if loc_total_capacity else 1
        self.gen_codes_and_names = get_gen_codes_and_names(
            db, self.gen_ids)
        self.gen_codes = list(self.gen_codes_and_names['gen_code'].values)
        self.gen_names = list(self.gen_codes_and_names['gen_name'].values)

        self.data_grouped_by_loc: pd.DataFrame = None
        self.gen_data: pd.DataFrame = None
        self.sta_data: pd.DataFrame = None
        self.data: pd.DataFrame = None
        self.data_aggregated_by_period: pd.DataFrame = None
        self.data_aggregated_by_loc_and_period: pd.DataFrame = None

    def _fill_missing_gen_data(self):

        date_range = pd.date_range(start=self.datetime_start, end=self.datetime_end, freq=self.data_freq)
        if date_range.empty:
            return
        all_time = pd.DataFrame({'data_date': date_range})
        if all_time.empty:
            return
        all_gens = pd.DataFrame({'gen_id': self.gen_ids})
        if all_gens.empty:
            return
        all_time = pd.merge(all_time, all_gens, how='cross')
        if all_time.empty:
            return
        self.gen_data = pd.merge(all_time, self.gen_data, left_on=[
                                 'data_date', 'gen_id'], right_on=['data_date', 'gen_id'], how='left')
        self.gen_data.set_index(
            [self.gen_data.data_date, self.gen_data.gen_id], inplace=True)
        self.gen_data.drop(['data_date', 'gen_id'], axis=1, inplace=True)

        self.gen_data['power'].fillna(self.gen_data['ac_production'], inplace=True)
        self.gen_data['ac_production'].fillna(self.gen_data['power'], inplace=True)

    def _fill_missing_sta_data(self):
        date_range = pd.date_range(start=self.datetime_start, end=self.datetime_end, freq=self.data_freq)
        if date_range.empty:
            return
        all_time = pd.DataFrame({'data_date': date_range})
        if all_time.empty:
            return
        all_gens = pd.DataFrame({'sta_id': [self.sta_id]})
        if all_gens.empty:
            return
        all_time = pd.merge(all_time, all_gens, how='cross')
        if all_time.empty:
            return
        self.sta_data = pd.merge(all_time, self.sta_data, left_on=[
                                 'data_date', 'sta_id'], right_on=['data_date', 'sta_id'], how='left')
        self.sta_data.set_index(
            [self.sta_data.data_date, self.sta_data.sta_id], inplace=True)
        self.sta_data.drop(['data_date', 'sta_id'], axis=1, inplace=True)

    def _merge_gen_and_sta_data(self):

        all_data = pd.DataFrame()
        for gen_id in self.gen_data.index.unique(level='gen_id'):
            aux_df = self.sta_data.copy()
            aux_df['gen_id'] = gen_id
            all_data = pd.concat([all_data, aux_df])

        self.data = self.gen_data.merge(all_data, left_on=['gen_id', 'data_date'], right_on=[
                                        'gen_id', 'data_date'], how='outer').reset_index().set_index(['gen_id', 'data_date'])

    def _get_specific_yield(self, rows):
        gen_id = rows.name[0]
        gen_rate_power = self.gen_codes_and_names.loc[gen_id]['gen_rate_power'] / 1000
        return rows['ac_production'] / gen_rate_power

    def _adjust_gen_units(self):
        self.gen_data['power'] = self.gen_data[['power']].apply(self._adjust_row_gen_units, axis=1)
        self.gen_data['ac_production'] = self.gen_data[['ac_production']].apply(self._adjust_row_gen_units, axis=1)
        self.gen_data['ac_production_prediction'] = self.gen_data[['ac_production_prediction']].apply(self._adjust_row_gen_units, axis=1)

    def _adjust_row_gen_units(self, row):
        row_start_date = row.name[1]
        row_end_date = get_period_end(row_start_date, self.data_freq, self.datetime_end)
        seconds_in_one_hour = 60*60
        seconds_in_row_period = (row_end_date - row_start_date).total_seconds() + 1
        divisor = seconds_in_one_hour / seconds_in_row_period
        row_value = row[0]
        if row_value is not None:
            return row_value / divisor / 1000

    def _adjust_sta_units(self):
        self.sta_data['irradiation'] = self.sta_data[['irradiation']].apply(self._adjust_row_sta_units, axis=1)

    def _adjust_row_sta_units(self, row):
        row_start_date = row.name[0]
        row_end_date = get_period_end(row_start_date, self.data_freq, self.datetime_end)
        seconds_in_one_hour = 60*60
        seconds_in_row_period = (row_end_date - row_start_date).total_seconds() + 1
        divisor = seconds_in_one_hour / seconds_in_row_period
        row_value = row[0]
        if row_value is not None:
            return row_value / divisor

    def _compute_calculated_columns(self):
        self.data['from'] = self.data.index.get_level_values(1)
        self.data['time_based_availability'] = (
            self.data['power'] == 0) & (self.data['irradiation'] > 0)
        self.data['count'] = 1
        self.data['is_missing'] = self.data['power'].isna()

    def _compute_agg_by_loc_and_period_calculated_columns(self):
        self.data_aggregated_by_loc_and_period['loc_specific_yield'] = self.data_aggregated_by_loc_and_period['ac_production'] / (
            self.loc_total_capacity / 1000)
        self.data_aggregated_by_loc_and_period['loc_performance_ratio'] = self.data_aggregated_by_loc_and_period.apply(
            lambda x: x['loc_specific_yield']/x['irradiation'] * 100 if x['irradiation'] != 0 else np.nan, axis=1)

        self.data_aggregated_by_loc_and_period.fillna(0, inplace=True)
        self.data_aggregated_by_loc_and_period['to'] = self.data_aggregated_by_loc_and_period.apply(
            self._get_group_period_end_date, axis=1)

    def _compute_agg_by_period_calculated_columns(self):
        self.data_aggregated_by_period['specific_yield'] = self.data_aggregated_by_period.apply(
            self._get_specific_yield, axis=1)
        self.data_aggregated_by_period['performance_ratio'] = self.data_aggregated_by_period.apply(
            lambda x: x['specific_yield']/x['irradiation'] * 100 if x['irradiation'] != 0 else np.nan, axis=1)

        self.data_aggregated_by_period['performance_ratio'].fillna(
            0, inplace=True)
        self.data_aggregated_by_period['to'] = self.data_aggregated_by_period.apply(
            self._get_group_period_end_date, axis=1)

    def fetch_data(self, db: Session):
        self.gen_data = get_gen_datas_grouped(db, self.cli_id, self.gen_ids, self.datetime_start, self.datetime_end, self.data_freq, {
                                              501: 'power', 502: 'ac_production', 508: 'ac_production_prediction'})

        self.sta_data = get_sta_datas_grouped(db, self.cli_id, self.sta_id, self.datetime_start, self.datetime_end, self.data_freq, {
                                              503: 'avg_ambient_temp', 504: 'avg_module_temp', 505: 'irradiation'})

        self._adjust_gen_units()
        self._adjust_sta_units()
        self._fill_missing_gen_data()
        self._fill_missing_sta_data()

        if self.gen_data.empty or self.sta_data.empty:
            return

        self._merge_gen_and_sta_data()
        self._compute_calculated_columns()

    def _get_group_period_end_date(self, rows):
        if self.freq:
            return get_period_end(rows['from'], self.freq, self.datetime_end)
        return self.datetime_end

    def _get_agg_unavailable(self, rows):
        periods = len(rows)
        return (periods - rows.sum()) / (periods)

    def fetch_aggregated_by_period(self, db: Session):
        if self.data is None:
            self.fetch_data(db)

        if self.data is None:
            return

        agg = {'power': 'sum', 'ac_production': 'sum', 'avg_ambient_temp': 'mean', 'avg_module_temp': 'mean',
               'irradiation': 'sum', 'time_based_availability': self._get_agg_unavailable, 'from': 'first', 'count': 'sum', 'is_missing': 'sum',
               'ac_production_prediction': 'sum'}

        if self.freq:
            self.data_aggregated_by_period = self.data.reset_index().set_index(
                'data_date').groupby(['gen_id', pd.Grouper(freq=self.freq)]).agg(agg)
        else:
            agg['data_date'] = 'first'
            self.data_aggregated_by_period = self.data.reset_index().set_index('gen_id').groupby('gen_id').agg(agg)

            self.data_aggregated_by_period.set_index(
                'data_date', append=True, inplace=True)

        self._compute_agg_by_period_calculated_columns()

    def fetch_aggregated_by_loc_and_period(self, db: Session):
        if self.data_aggregated_by_period is None:
            self.fetch_aggregated_by_period(db)

        if self.data is None:
            return

        agg = {'power': 'sum', 'ac_production': 'sum', 'avg_ambient_temp': 'mean', 'avg_module_temp': 'mean',
               'irradiation': 'mean', 'from': 'first', 'time_based_availability': 'mean', 'performance_ratio': 'mean', 'specific_yield': 'sum',
               'ac_production_prediction': 'sum'}

        self.data_aggregated_by_loc_and_period = self.data_aggregated_by_period.groupby(
            'data_date').agg(agg)

        self._compute_agg_by_loc_and_period_calculated_columns()
