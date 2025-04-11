
import datetime
from typing import List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import pytz
from db.utils import (get_gen_data, get_gen_ids_by_data_pro_id, get_location,
                      get_sta_data, insert_or_update_predictions)
from pysolar.solar import *
from sqlalchemy import Float
from sqlalchemy.orm import Session

TARGET_COLUMN = 'Generated Power'


class Model:
    def __init__(self, cat_boost_model, features, x_scaler, y_scaler, trained_capacity):
        self.cat_boost_model = cat_boost_model
        self.features = features
        self.x_scaler = x_scaler
        self.y_scaler = y_scaler
        self.trained_capacity = trained_capacity
        self.prediction_capacity = None

    def save(self, path):
        joblib.dump(self, path)

    def generate_input(self, loc_latitude: int, loc_longitude: int, data: pd.DataFrame) -> pd.DataFrame:
        data['Generated Power'] = data['Generated Power'] * 1000 * 4
        data['Shortwave Radiation'] = data['Shortwave Radiation'] * 1000
        data = add_calculated_features(data, loc_latitude, loc_longitude)
        data = data[self.features]
        data[f'{TARGET_COLUMN} {1} Hour Lag'] = data[f'{TARGET_COLUMN} {1} Hour Lag'] * self.trained_capacity / self.prediction_capacity
        return data

    def predict(self, data):
        data = data.dropna()
        indexes = data.index
        data = self.x_scaler.transform(data)
        prediction = self.cat_boost_model.predict(data)
        prediction = self.y_scaler.inverse_transform(prediction.reshape(-1, 1))
        prediction = prediction * self.prediction_capacity / self.trained_capacity
        prediction = np.where(prediction < 0, 0, prediction)
        prediction = prediction / 4000
        prediction = np.round(prediction, 3)
        prediction = [x[0] for x in prediction]
        return pd.DataFrame(prediction, index=indexes, columns=['Prediction'])


def load_model(path, prediction_capacity: Float) -> Model:
    model = joblib.load(path)
    model.prediction_capacity = prediction_capacity
    return model


def get_data(db: Session,
             start_date: Optional[datetime.datetime],
             end_date: Optional[datetime.datetime],
             cli_id: Optional[int] = None,
             loc_id: Optional[int] = None,
             gen_id: Optional[int] = None,
             data_pro_id: Optional[int] = None) -> Tuple[pd.DataFrame, int, int, int, datetime.datetime, datetime.datetime, Float, Float, Float]:
    if not data_pro_id and not (cli_id and loc_id and gen_id and start_date and end_date):
        raise ValueError('Invalid parameters: either data_pro_id or cli_id, loc_id, gen_id, start_date and end_date must be provided')

    gen_ids = None
    if data_pro_id:
        cli_id, loc_id, gen_ids, start_date, end_date = get_gen_ids_by_data_pro_id(db, data_pro_id)
        if cli_id is None:
            return pd.DataFrame(), None, None, None, None, None, None, None, None
        gen_id = gen_ids[0]

    if isinstance(start_date, int):
        start_date = datetime.datetime.fromtimestamp(start_date)
    if isinstance(end_date, int):
        end_date = datetime.datetime.fromtimestamp(end_date)

    start_date = start_date - datetime.timedelta(hours=2)
    location = get_location(db, loc_id, cli_id)
    capacity = location.loc_output_total_capacity
    latitude = location.loc_coord_lat
    longitude = location.loc_coord_lng
    gen_df = get_gen_data(db, cli_id, gen_id, start_date, end_date)
    sta_df = get_sta_data(db, cli_id, loc_id, start_date, end_date)
    model_df = pd.merge(gen_df, sta_df, left_index=True, right_index=True, how='outer')
    return model_df, cli_id, loc_id, gen_id, start_date, end_date, capacity, latitude, longitude


def resample_data(model_df: pd.DataFrame) -> pd.DataFrame:
    model_df.dropna(inplace=True)
    model_df['count'] = 1
    model_df = model_df.resample('1H', label='right', closed='right').agg({'Temperature': np.mean,
                                                                           'Shortwave Radiation': np.sum,
                                                                           'Cloud Cover Total': np.mean,
                                                                           'Precipitation Total': np.sum,
                                                                           'Generated Power': np.mean,
                                                                           'count': np.sum}).ffill()
    model_df = model_df[model_df['count'] >= 4]
    model_df = model_df[['Temperature', 'Precipitation Total', 'Cloud Cover Total', 'Shortwave Radiation', 'Generated Power']]
    return model_df


def add_temporal_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df['hour'] = df.index.hour
    df['month'] = df.index.month
    df['day'] = df.index.day

    df['season'] = df['month'].apply(lambda x: 0 if x in [12, 1, 2] else (1 if x in [3, 4, 5] else (2 if x in [6, 7, 8] else 3)))

    df = pd.concat([df, pd.get_dummies(df['season'], prefix='season')], axis=1)
    df = pd.concat([df, pd.get_dummies(df['month'], prefix='month')], axis=1)
    df = pd.concat([df, pd.get_dummies(df['hour'], prefix='hour')], axis=1)
    # Add missing month columns
    for i in range(1, 13):
        if f'month_{i}' not in df.columns:
            df[f'month_{i}'] = 0
    # Add missing hour columns
    for i in range(0, 24):
        if f'hour_{i}' not in df.columns:
            df[f'hour_{i}'] = 0
    # Add missing season columns
    for i in range(0, 4):
        if f'season_{i}' not in df.columns:
            df[f'season_{i}'] = 0
    df.drop(['season', 'month', 'hour'], axis=1, inplace=True)

    return df


def add_lag_based_feature_generation(df: pd.DataFrame) -> pd.DataFrame:
    df[f'{TARGET_COLUMN} {1} Hour Lag'] = df[TARGET_COLUMN].shift(1)
    return df


def add_hours_since_last_rain(df: pd.DataFrame) -> pd.DataFrame:
    df['Hours Since Last Rain'] = 0
    last_rain_date = None
    for index, row in df.iterrows():
        if row['Precipitation Total'] > 0:
            df.at[index, 'Hours Since Last Rain'] = 0
            last_rain_date = index
        else:
            if last_rain_date is None:
                df.at[index, 'Hours Since Last Rain'] = 0
            else:
                df.at[index, 'Hours Since Last Rain'] = (index - last_rain_date).total_seconds() / 3600
    return df


def get_solar_zenith_angle(row, tz, latitude: Float, longitude: Float) -> float:
    time = tz.localize(row.name)
    sza = get_altitude(latitude, longitude, time)
    return sza


def add_solar_zenith_angle(df, latitude: Float, longitude: Float) -> pd.DataFrame:
    tz = pytz.timezone('America/Montevideo')
    df['Solar Zenith Angle'] = df.apply(lambda row: get_solar_zenith_angle(row, tz, latitude, longitude), axis=1)
    return df


def add_calculated_features(df, latitude: Float, longitude: Float) -> pd.DataFrame:
    df = add_temporal_feature_engineering(df)
    df = add_lag_based_feature_generation(df)
    df = add_hours_since_last_rain(df)
    df = add_solar_zenith_angle(df, latitude, longitude)
    df = df.drop(columns=[TARGET_COLUMN])
    return df


def save_predictions(db: Session, cli_id: int, gen_id: int, predictions: List[Tuple[datetime.datetime, float, int]]):
    insert_or_update_predictions(db, cli_id, gen_id, predictions)
