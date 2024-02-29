from datetime import datetime
import json
from typing import List, Optional, Tuple
from core.solar import Solar
from db.utils import get_client_settings, get_gen_ids_by_data_pro_id, insert_cli_gen_alerts
from db.db import session

ALERT_DATA_TYPE = 1
ALERT_1_DEFAULT_THRESHOLD = 90
ALERT_2_DEFAULT_THRESHOLD = 94
ALERT_3_DEFAULT_THRESHOLD = 90
MAX_DATA_PER_DAY = 24 * 60 / 15

def calculate_alerts(datetime_start: Optional[datetime], datetime_end: Optional[datetime], data_pro_id: Optional[int] = None, cli_id: Optional[int] = None, loc_id: Optional[int] = None) -> Tuple[int, int, List[int], datetime, datetime, int]:

    if not data_pro_id and not (cli_id and loc_id and datetime_start and datetime_end):
        raise ValueError('Invalid parameters: either data_pro_id or cli_id, loc_id, datetime_start and datetime_end must be provided')
    gen_ids = None
    if data_pro_id:
        cli_id, loc_id, gen_ids, datetime_start, datetime_end = get_gen_ids_by_data_pro_id(session, data_pro_id)

    solar = Solar(cli_id=cli_id, loc_id=loc_id,datetime_start=datetime_start, datetime_end=datetime_end, freq='1D', gen_ids=gen_ids, sta_id=None)
    solar.fetch_aggregated_by_period()
    data = solar.data_aggregated_by_period
    
    cli_settings = get_client_settings(session, cli_id)
    alert_1_threshold = 100 - (int(cli_settings.loc['alertDataAvailabilityLowerThan']['cli_set_value']) if 'alertDataAvailabilityLowerThan' in cli_settings.index else ALERT_1_DEFAULT_THRESHOLD)
    alert_2_threshold = 100 - (int(cli_settings.loc['alertPerformanceRatioLowerThan']['cli_set_value']) if 'alertPerformanceRatioLowerThan' in cli_settings.index else ALERT_2_DEFAULT_THRESHOLD)
    alert_3_threshold = 100 - (int(cli_settings.loc['alertTimeBasedAvailabilityLowerThan']['cli_set_value']) if 'alertTimeBasedAvailabilityLowerThan' in cli_settings.index else ALERT_3_DEFAULT_THRESHOLD)

    data['prev_performance_ratio'] = data['performance_ratio'].shift(1)
    data['prev_time_based_availability'] = data['time_based_availability'].shift(1)
    data['prev_missing'] = data['is_missing'].shift(1)

    data['performance_ratio_diff_percentage'] = 100 - (data['performance_ratio']  / data['prev_performance_ratio'] ) * 100
    data['time_based_availability_diff_percentage'] = 100 - (data['time_based_availability']  / data['prev_time_based_availability'] ) *100
    data['missing_percentage'] = 100 - ( (MAX_DATA_PER_DAY - data['prev_missing']) / MAX_DATA_PER_DAY ) *100

    for i, rows in data.groupby(level=0):
        alert_1 = rows['missing_percentage'] >= alert_1_threshold
        alert_2 = rows['performance_ratio_diff_percentage'] >= alert_2_threshold
        alert_3 = rows['time_based_availability_diff_percentage'] >= alert_3_threshold
        
        data.loc[i, 'alert_1'] = alert_1
        data.loc[i, 'alert_2'] = alert_2
        data.loc[i, 'alert_3'] = alert_3

    rows_to_insert = []
    now = datetime.utcnow()
    for i, alert in data.iterrows():            
        gen_id = i[0]
        date = i[1]
        gen_code= solar.gen_codes_and_names.loc[gen_id, 'gen_code']
        if alert['alert_1']:
            description = f"Data availability on {date.strftime('%Y-%m-%d')} for generator {gen_code} was {100 - alert['missing_percentage']:.0f}%."
            alert_data = {'type': 'alertDataAvailabilityLow', 'gen_code': gen_code, "description": description, 'value': 100 - alert['missing_percentage'], "previous_value": None, 'threshold': alert_1_threshold, "date": date.strftime('%Y-%m-%d')}
            rows_to_insert.append({"cli_id": cli_id, "gen_id": gen_id, "cli_gen_alert_added": now, "cli_gen_alert_type": ALERT_DATA_TYPE, "cli_gen_alert_data": json.dumps(alert_data), "cli_gen_alert_trigger": date})
        if alert['alert_2']:
            description = f"Performance ratio on {date.strftime('%Y-%m-%d')} for generator {gen_code} was {alert['performance_ratio']:.0f}%, which is {alert['performance_ratio_diff_percentage']:.0f}% lower than the previous day ({alert['prev_performance_ratio']:.0f}%)"
            alert_data = {'type': 'alertPerformanceRatioLow', 'gen_code': gen_code, 'description:': description, 'value': alert['performance_ratio'], "previous_value": alert['prev_performance_ratio'], 'threshold': alert_2_threshold, "date": date.strftime('%Y-%m-%d'), "diff_percentage": alert['performance_ratio_diff_percentage']}
            rows_to_insert.append({"cli_id": cli_id, "gen_id": gen_id, "cli_gen_alert_added": now, "cli_gen_alert_type": ALERT_DATA_TYPE, "cli_gen_alert_data": json.dumps(alert_data), "cli_gen_alert_trigger": date})
        if alert['alert_3']:
            description = f"Time based availability on {date.strftime('%Y-%m-%d')} for generator {gen_code} was {alert['time_based_availability']*100:.0f}%, which is { alert['time_based_availability_diff_percentage']:.0f}% lower than the previous day ({alert['prev_time_based_availability']*100:.0f}%)"
            alert_data = {'type': 'alertTimeBasedAvailabilityLow', 'gen_code': gen_code, 'description':description,'value': alert['time_based_availability'], "previous_value": alert['prev_time_based_availability'], 'threshold': alert_3_threshold, "date": date.strftime('%Y-%m-%d'), "diff_percentage": alert['time_based_availability_diff_percentage']}
            rows_to_insert.append({"cli_id": cli_id, "gen_id": gen_id, "cli_gen_alert_added": now, "cli_gen_alert_type": ALERT_DATA_TYPE, "cli_gen_alert_data": json.dumps(alert_data), "cli_gen_alert_trigger": date})

    insert_cli_gen_alerts(session, cli_id,  solar.gen_ids, datetime_start, datetime_end, rows_to_insert)     

    return cli_id, loc_id, solar.gen_ids, datetime_start, datetime_end, len(rows_to_insert)

    