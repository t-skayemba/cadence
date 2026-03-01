import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

def parse_health_export(zip_path):
    sleep_records = []
    step_records = []
    heart_rate_records = []

    with zipfile.ZipFile(zip_path, 'r') as z:
        with z.open('apple_health_export/export.xml') as f:
            for event, elem in ET.iterparse(f, events=['end']):
                if elem.tag != 'Record':
                    elem.clear()
                    continue

                record_type = elem.get('type')
                start = elem.get('startDate')
                end = elem.get('endDate')
                value = elem.get('value')

                if record_type == 'HKCategoryTypeIdentifierSleepAnalysis':
                    if 'Asleep' in value:
                        sleep_records.append({
                            'start': start,
                            'end': end
                        })
                elif record_type == 'HKQuantityTypeIdentifierStepCount':
                    step_records.append({
                        'start': start,
                        'end': end,
                        'value': float(value)
                    })
                elif record_type == 'HKQuantityTypeIdentifierHeartRate':
                    heart_rate_records.append({
                        'start': start,
                        'value': float(value)
                    })
                elem.clear()
    
    return sleep_records, step_records, heart_rate_records