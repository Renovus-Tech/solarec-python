import datetime
from typing import List, Optional

from pydantic import BaseModel


class GenDataBase(BaseModel):

    cli_id: int
    gen_id: int
    data_date: int
    data_type_id: int
    data_pro_id: int
    data_value: float
    data_date_added: datetime.datetime


class StaDataBase(BaseModel):

    cli_id: int
    sta_id: int
    data_date: int
    data_type_id: int
    data_pro_id: int
    data_value: float
    data_date_added: datetime.datetime


class LocDataBase(BaseModel):

    cli_id: int
    loc_id: int
    data_date: int
    data_type_id: int
    data_pro_id: int
    data_value: float
    data_date_added: datetime.datetime


class LocDataCreate(LocDataBase):
    pass
