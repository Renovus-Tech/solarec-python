from datetime import datetime, timedelta
from typing import List
import numpy as np
import pandas as pd
from db.utils import get_gen_codes_and_names, get_gen_datas_grouped, get_gen_ids_by_loc_id, get_period_end, get_sta_datas_grouped, get_sta_id_by_loc_id, get_loc_output_capacity, insert_cli_gen_alerts
from db.db import session


class Solar():
    def __init__(self, cli_id: int, loc_id: int, gen_ids: List[int], sta_id: int,  datetime_start: datetime, datetime_end: datetime, freq: str):
        self.loc_id = loc_id
        self.gen_ids = gen_ids if gen_ids else [
            int(x) for x in get_gen_ids_by_loc_id(session, loc_id)['gen_id_auto'].values]
        self.sta_id = sta_id if sta_id else int(
            get_sta_id_by_loc_id(session, loc_id)['sta_id_auto'][0])
        self.datetime_start = datetime_start
        self.datetime_end = datetime_end
        self.data: pd.DataFrame
        self.cli_id = cli_id
        self.freq = freq if freq else '10Y'

        loc_total_capacity = get_loc_output_capacity(session, self.loc_id)
        self.loc_total_capacity = loc_total_capacity if loc_total_capacity else 1
        self.gen_codes_and_names = get_gen_codes_and_names(
            session, self.gen_ids)
        self.gen_codes = list(self.gen_codes_and_names['gen_code'].values)
        self.gen_names = list(self.gen_codes_and_names['gen_name'].values)

        self.data_grouped_by_loc: pd.DataFrame = None
        self.gen_data: pd.DataFrame = None
        self.sta_data: pd.DataFrame = None
        self.data: pd.DataFrame = None
        self.data_aggregated_by_period: pd.DataFrame = None
        self.data_aggregated_by_loc_and_period: pd.DataFrame = None

    def _fill_missing_gen_data(self):
        all_time = pd.DataFrame({'data_date': np.arange(
            self.datetime_start, self.datetime_end, timedelta(minutes=15))})
        all_gens = pd.DataFrame({'gen_id': self.gen_ids})
        all_time = pd.merge(all_time, all_gens, how='cross')
        self.gen_data = pd.merge(all_time, self.gen_data, left_on=[
                                 'data_date', 'gen_id'], right_on=['data_date', 'gen_id'], how='left')
        self.gen_data.set_index(
            [self.gen_data.data_date, self.gen_data.gen_id], inplace=True)
        self.gen_data.drop(['data_date', 'gen_id'], axis=1, inplace=True)

        self.gen_data['power'] = self.gen_data['power'].fillna(self.gen_data['ac_production'])

    def _fill_missing_sta_data(self):
        all_time = pd.DataFrame({'data_date': np.arange(
            self.datetime_start, self.datetime_end, timedelta(minutes=15))})
        all_gens = pd.DataFrame({'sta_id': [self.sta_id]})
        all_time = pd.merge(all_time, all_gens, how='cross')
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

    def _adjust_units(self):
        self.gen_data['power'] = self.gen_data['power'] / 4000
        self.gen_data['ac_production'] = self.gen_data['ac_production'] / 4000
        self.sta_data['irradiation'] = self.sta_data['irradiation'] / 4

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

    def fetch_data(self):
        self.gen_data = get_gen_datas_grouped(session, self.cli_id, self.gen_ids, self.datetime_start, self.datetime_end, {
                                              501: 'power', 502: 'ac_production'})

        self.sta_data = get_sta_datas_grouped(session, self.cli_id, self.sta_id, self.datetime_start, self.datetime_end, {
                                              503: 'avg_ambient_temp', 504: 'avg_module_temp', 505: 'irradiation'})

        self._adjust_units()
        self._fill_missing_gen_data()
        self._fill_missing_sta_data()

        self._merge_gen_and_sta_data()
        self._compute_calculated_columns()

    def _get_group_period_end_date(self, rows):
        return get_period_end(rows['from'], self.freq, self.datetime_end)

    def _get_agg_unavailable(self, rows):
        periods = len(rows)
        return (periods - rows.sum()) / (periods)

    def fetch_aggregated_by_period(self):
        if self.data is None:
            self.fetch_data()

        agg = {'power': 'sum', 'ac_production': 'sum', 'avg_ambient_temp': 'mean', 'avg_module_temp': 'mean',
               'irradiation': 'sum', 'time_based_availability': self._get_agg_unavailable, 'from': 'first', 'count': 'sum', 'is_missing': 'sum'}

        self.data_aggregated_by_period = self.data.reset_index().set_index(
            'data_date').groupby(['gen_id', pd.Grouper(freq=self.freq)]).agg(agg)

        self._compute_agg_by_period_calculated_columns()

    def fetch_aggregated_by_loc_and_period(self):
        if self.data_aggregated_by_period is None:
            self.fetch_aggregated_by_period()

        agg = {'power': 'sum', 'ac_production': 'sum', 'avg_ambient_temp': 'mean', 'avg_module_temp': 'mean',
               'irradiation': 'mean', 'from': 'first', 'time_based_availability': 'mean', 'performance_ratio': 'mean', 'specific_yield': 'sum'}

        self.data_aggregated_by_loc_and_period = self.data_aggregated_by_period.groupby(
            'data_date').agg(agg)

        self._compute_agg_by_loc_and_period_calculated_columns()

