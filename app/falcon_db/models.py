from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey

from .db import Base


class Client(Base):
    __tablename__ = "client"

    cli_id_auto = Column(Integer, primary_key=True)
    cli_name = Column(String)
    cli_name_legal = Column(String)
    cli_name_address = Column(String)
    cli_flags = Column(String)


class Location(Base):
    __tablename__ = "location"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    loc_id_auto = Column(Integer, primary_key=True)
    data_def_id = Column(Integer)
    loc_name = Column(String)
    loc_address = Column(String)
    loc_coord_lat = Column(Float)
    loc_coord_lng = Column(Float)
    loc_flags = Column(String)
    loc_code = Column(String)
    loc_output_capacity = Column(Float)
    loc_output_total_capacity = Column(Float)
    loc_reference_density = Column(Float)
    loc_data_date_max = Column(DateTime(timezone=False))
    loc_data_date_min = Column(DateTime(timezone=False))
    loc_demo_date = Column(DateTime(timezone=False))


class Station(Base):
    __tablename__ = "station"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    sta_id_auto = Column(Integer, primary_key=True)
    data_def_id = Column(Integer)
    loc_id = Column(Integer, ForeignKey("location.loc_id_auto"))
    sta_name = Column(String)
    sta_description = Column(String)
    sta_coord_lat = Column(Float)
    sta_coord_lng = Column(Float)
    sta_flags = Column(String)
    sta_code = Column(String)
    sta_data_date_max = Column(DateTime(timezone=False))
    sta_data_date_min = Column(DateTime(timezone=False))


class Generator(Base):
    __tablename__ = "generator"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    gen_id_auto = Column(Integer, primary_key=True)
    data_def_id = Column(Integer)
    loc_id = Column(Integer, ForeignKey("location.loc_id"))
    gen_name = Column(String)
    gen_description = Column(String)
    gen_coord_lat = Column(Float)
    gen_coord_lng = Column(Float)
    gen_brand = Column(String)
    gen_model = Column(String)
    gen_serial_num = Column(String)
    gen_rate_power = Column(Float)
    gen_flags = Column(String)
    gen_code = Column(String)
    gen_data_date_max = Column(DateTime(timezone=False))
    gen_data_date_min = Column(DateTime(timezone=False))


class GenData(Base):
    __tablename__ = "gen_data"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    gen_id = Column(Integer, ForeignKey("generator.gen_id_auto"), primary_key=True)
    data_date = Column(DateTime, primary_key=True)
    data_type_id = Column(Integer, primary_key=True)
    data_pro_id = Column(Integer, ForeignKey("data_processing.data_pro_id_auto"))
    data_value = Column(Float)
    data_date_added = Column(DateTime(timezone=True))


class StaData(Base):
    __tablename__ = "sta_data"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    sta_id = Column(Integer, ForeignKey("station.sta_id_auto"), primary_key=True)
    data_date = Column(DateTime, primary_key=True)
    data_type_id = Column(Integer, primary_key=True)
    data_pro_id = Column(Integer, ForeignKey("data_processing.data_pro_id_auto"))
    data_value = Column(Float)
    data_date_added = Column(DateTime(timezone=True))


class LocData(Base):
    __tablename__ = "loc_data"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    loc_id = Column(Integer, ForeignKey("location.loc_id_auto"), primary_key=True)
    data_date = Column(DateTime, primary_key=True)
    data_type_id = Column(Integer, primary_key=True)
    data_pro_id = Column(Integer, ForeignKey("data_processing.data_pro_id_auto"))
    data_value = Column(Float)
    data_date_added = Column(DateTime(timezone=True))


class GenPower(Base):
    __tablename__ = "gen_power"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    gen_id = Column(Integer, ForeignKey("generator.gen_id_auto"), primary_key=True)
    pwr_wind_speed = Column(Float, primary_key=True)
    pwr_air_density = Column(Float, primary_key=True)
    gen_power = Column(Float)


class DataProcessing(Base):
    __tablename__ = "data_processing"

    data_pro_id_auto = Column(Integer, primary_key=True)
    data_def_id = Column(Integer)
    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"))
    loc_id = Column(Integer, ForeignKey("location.loc_id_auto"))
    data_pro_file_name = Column(String)
    data_pro_date_start = Column(DateTime(timezone=True))
    data_pro_date_end = Column(DateTime(timezone=True))
    data_pro_result = Column(Integer)
    data_pro_file_log = Column(String)


class StatProcessing(Base):
    __tablename__ = "stat_processing"

    stat_pro_id_auto = Column(Integer, primary_key=True)
    stat_def_id = Column(Integer)
    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"))
    stat_pro_date_start = Column(DateTime(timezone=True))
    stat_pro_date_end = Column(DateTime(timezone=True))
    stat_pro_result = Column(Integer)
    stat_pro_file_log = Column(String)
    stat_pro_type = Column(Integer)


class DataType(Base):
    __tablename__ = "data_type"

    data_type_id = Column(Integer, primary_key=True)
    data_type_name = Column(String)
    data_type_units = Column(String)
    data_type_description = Column(String)


class LocStatistic(Base):
    __tablename__ = "loc_statistic"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    loc_id = Column(Integer, ForeignKey("location.loc_id_auto"), primary_key=True)
    stat_date = Column(DateTime(timezone=True), primary_key=True)
    stat_type_id = Column(Integer, primary_key=True)
    stat_pro_id = Column(Integer, ForeignKey("stat_processing.stat_pro_id_auto"))
    stat_value = Column(Float)
    stat_date_added = Column(DateTime(timezone=True))


class GenAlarm(Base):
    __tablename__ = "gen_alarm"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    gen_id = Column(Integer, ForeignKey("generator.gen_id_auto"), primary_key=True)
    alarm_code = Column(Float, primary_key=True)
    alarm_description = Column(String)
    data_cat_id = Column(Integer, ForeignKey("data_category.data_cat_id_auto"), primary_key=True)


class LocGenAlarm(Base):
    __tablename__ = "loc_gen_alarm"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    loc_id = Column(Integer, ForeignKey("location.loc_id_auto"), primary_key=True)
    alarm_code = Column(Float, primary_key=True)
    alarm_description = Column(String)
    data_cat_id = Column(Integer, ForeignKey("data_category.data_cat_id_auto"), primary_key=True)


class CliGenAlarm(Base):
    __tablename__ = "cli_gen_alarm"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    alarm_code = Column(Float, primary_key=True)
    alarm_description = Column(String)
    data_cat_id = Column(Integer, ForeignKey("data_category.data_cat_id_auto"), primary_key=True)


class GenAlert(Base):
    __tablename__ = "gen_alert"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    gen_id = Column(Integer, ForeignKey("generator.gen_id_auto"), primary_key=True)
    alert_def_id = Column(
        Integer, ForeignKey("alert_definition.alert_def_id_auto"), primary_key=True
    )
    alert_date_added = Column(DateTime(timezone=True), primary_key=True)
    alert_date_send = Column(DateTime(timezone=True))
    alert_message = Column(String, primary_key=True)
    alert_pro_id = Column(Integer, ForeignKey("alert_processing.alert_pro_id_auto"))


class LocAlert(Base):
    __tablename__ = "loc_alert"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    loc_id = Column(Integer, ForeignKey("location.loc_id_auto"), primary_key=True)
    alert_def_id = Column(
        Integer, ForeignKey("alert_definition.alert_def_id_auto"), primary_key=True
    )
    alert_date_added = Column(DateTime(timezone=True), primary_key=True)
    alert_date_send = Column(DateTime(timezone=True))
    alert_message = Column(String, primary_key=True)
    alert_pro_id = Column(Integer, ForeignKey("alert_processing.alert_pro_id_auto"))


class StaAlert(Base):
    __tablename__ = "sta_alert"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    sta_id = Column(Integer, ForeignKey("station.sta_id_auto"), primary_key=True)
    alert_def_id = Column(
        Integer, ForeignKey("alert_definition.alert_def_id_auto"), primary_key=True
    )
    alert_date_added = Column(DateTime(timezone=True), primary_key=True)
    alert_date_send = Column(DateTime(timezone=True))
    alert_message = Column(String, primary_key=True)
    alert_pro_id = Column(Integer, ForeignKey("alert_processing.alert_pro_id_auto"))


class LocEstimation(Base):
    __tablename__ = "loc_estimation"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    loc_id = Column(Integer, ForeignKey("location.loc_id_auto"), primary_key=True)
    loc_est_id_auto = Column(Integer, primary_key=True)
    loc_est_order = Column(Integer)
    loc_est_title = Column(String)
    loc_est_01 = Column(Float)
    loc_est_02 = Column(Float)
    loc_est_03 = Column(Float)
    loc_est_04 = Column(Float)
    loc_est_05 = Column(Float)
    loc_est_06 = Column(Float)
    loc_est_07 = Column(Float)
    loc_est_08 = Column(Float)
    loc_est_09 = Column(Float)
    loc_est_10 = Column(Float)
    loc_est_11 = Column(Float)
    loc_est_12 = Column(Float)


class LocDataMdlMlSanitized(Base):
    __tablename__ = "loc_data_mdl_ml_sanitized"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    loc_id = Column(Integer, ForeignKey("location.loc_id_auto"), primary_key=True)
    data_pro_id = Column(Integer, ForeignKey("data_processing.data_pro_id_auto"))
    data_stat_id = Column(Integer)
    data_date = Column(DateTime, primary_key=True)
    data_value_401 = Column(Float)
    data_value_402 = Column(Float)
    data_date_added = Column(DateTime(timezone=True))


class GenDataMdlMlSanitized(Base):
    __tablename__ = "gen_data_mdl_ml_sanitized"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    loc_id = Column(Integer, ForeignKey("location.loc_id_auto"), primary_key=True)
    gen_id = Column(Integer, ForeignKey("generator.gen_id_auto"), primary_key=True)
    data_pro_id = Column(Integer, ForeignKey("data_processing.data_pro_id_auto"))
    data_stat_id = Column(Integer)
    data_date = Column(DateTime, primary_key=True)
    data_value_201 = Column(Float)
    data_value_202 = Column(Float)
    data_value_204 = Column(Float)
    data_value_205 = Column(Float)
    data_value_257 = Column(Float)
    data_date_added = Column(DateTime(timezone=True))


class StaDataMdlMlSanitized(Base):
    __tablename__ = "sta_data_mdl_ml_sanitized"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    loc_id = Column(Integer, ForeignKey("location.loc_id_auto"), primary_key=True)
    sta_id = Column(Integer, ForeignKey("station.sta_id_auto"), primary_key=True)
    data_pro_id = Column(Integer, ForeignKey("data_processing.data_pro_id_auto"))
    data_stat_id = Column(Integer)
    data_date = Column(DateTime, primary_key=True)
    data_value_303 = Column(Float)
    data_value_304 = Column(Float)
    data_value_305 = Column(Float)
    data_date_added = Column(DateTime(timezone=True))


class GenNeighbour(Base):
    __tablename__ = "gen_neighbour"

    cli_id = Column(Integer, ForeignKey("client.cli_id_auto"), primary_key=True)
    gen_id = Column(Integer, ForeignKey("generator.gen_id_auto"), primary_key=True)
    gen_id_neighbour = Column(Integer, ForeignKey("generator.gen_id_auto"), primary_key=True)
    gen_id_neighbour_position = Column(Integer, primary_key=True)


class DataCategory(Base):
    __tablename__ = "data_category"

    data_cat_id_auto = Column(Integer, primary_key=True)
    data_cat_name = Column(String)
    data_cat_description = Column(String)


class LocDataWeather(Base):
    __tablename__ = "loc_data_weather"

    cli_id = Column(Integer, ForeignKey("client.cli_id"), primary_key=True)
    loc_id = Column(Integer, ForeignKey("client.loc_id"), primary_key=True)
    data_date = Column(DateTime, primary_key=True)
    data_type_id = Column(Integer, primary_key=True)
    data_value = Column(Float)
    data_date_added = Column(DateTime(timezone=True), primary_key=True)
