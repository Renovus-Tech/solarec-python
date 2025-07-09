import datetime
import logging
import time
import uuid

from sqlalchemy.orm import Session
from db.db import get_db
from db.utils import get_date_intervals_without_data, insert_irradiation_per_month, insert_production_per_month

logging.basicConfig(level=logging.INFO)

PROCESS_ID = str(uuid.uuid4())
SCHEDULER_INTERVAL_SECONDS = 60 * 60 * 24  # 24 hours
DB_NAME = "renovus_grinplus"
logging.info("Process ID: %s", PROCESS_ID)
logging.info("Background process for import data started.")
while True:
    db = None
    db_gen = None
    try:
        db_gen = get_db()
        db: Session = next(db_gen)
        start_date = datetime.datetime(2025, 3, 1)
        end_date = datetime.datetime.now()  # Use current date as end date
        if db.bind.url.database != DB_NAME:  # Ensure we are connected to the correct database
            raise Exception(f"Connected to wrong database: {db.bind.url.database}. Expected: {DB_NAME}")
        date_intervals = get_date_intervals_without_data(db, start_date, end_date)
        for start, end in date_intervals:
            logging.info("Insert irradiation per month.")
            insert_irradiation_per_month(db, start, end)
            logging.info("Insert production per month.")
            insert_production_per_month(db, start, end)

        # Success - close db and sleep
        logging.info("Process completed successfully. Sleeping for %s seconds.", SCHEDULER_INTERVAL_SECONDS)
        if db:
            db.close()
        if db_gen:
            try:
                next(db_gen)
            except StopIteration:
                pass
        time.sleep(SCHEDULER_INTERVAL_SECONDS)

    except Exception as e:
        logging.error("An error occurred while importing data: %s", e)
        logging.info("Retrying without sleep...")
        # Close db connection on error
        if db:
            try:
                db.close()
            except Exception:
                pass
        if db_gen:
            try:
                next(db_gen)
            except StopIteration:
                pass
