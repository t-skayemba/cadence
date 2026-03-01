from datetime import datetime
from collections import defaultdict

def parse_date(date_str):
    return datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')

def get_activity_distribution(step_records):
    hourly_totals = defaultdict(float)
    hourly_counts = defaultdict(int)

    for record in step_records:
        hour = parse_date(record['start']).hour
        hourly_totals[hour] += record['value']
        hourly_counts[hour] += 1

    distribution = []
    for hour in range(24):
        if hourly_counts[hour] > 0:
            distribution.append(round(hourly_totals[hour] / hourly_counts[hour], 2))
        else:
            distribution.append(0)
    return distribution

def get_peak_hours(distribution):
    max_val = max(distribution)
    peak_hour = distribution.index(max_val)
    return peak_hour

def get_crash_hour(distribution):
    waking_hours = distribution[7:22]
    min_val = min(waking_hours)
    crash_hour = waking_hours.index(min_val) + 7
    return crash_hour

def get_sleep_metrics(sleep_records):
    if not sleep_records:
        return {
            'avg_duration': 0,
            'avg_bedtime': 'No data',
            'avg_wake_time': 'No data',
            'consistency_score': 0
        }

    durations = []
    bedtimes = []
    wake_times = []

    for record in sleep_records:
        start = parse_date(record['start'])
        end = parse_date(record['end'])
        duration = (end - start).total_seconds() / 3600

        if 3 <= duration <= 12:
            durations.append(duration)
            bedtimes.append(start.hour + start.minute / 60)
            wake_times.append(end.hour + end.minute / 60)

    if not durations:
        return {
            'avg_duration': 0,
            'avg_bedtime': 'No data',
            'avg_wake_time': 'No data',
            'consistency_score': 0
        }

    avg_duration = round(sum(durations) / len(durations), 1)

    def normalize_bedtime(h):
        return h + 24 if h < 6 else h

    normalized_bedtimes = [normalize_bedtime(b) for b in bedtimes]
    avg_bedtime = (sum(normalized_bedtimes) / len(normalized_bedtimes)) % 24
    avg_wake = sum(wake_times) / len(wake_times)

    bedtime_std = (sum(
        (normalize_bedtime(b) - (sum(normalized_bedtimes) / len(normalized_bedtimes))) ** 2
        for b in bedtimes
    ) / len(bedtimes))
    consistency = max(0, round(10 - (bedtime_std / 30 * 60), 1))

    def format_time(decimal_hour):
        hour = int(decimal_hour) % 24
        minute = int((decimal_hour % 1) * 60)
        period = 'AM' if hour < 12 else 'PM'
        display_hour = hour if hour <= 12 else hour - 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour}:{minute:02d} {period}"

    return {
        'avg_duration': avg_duration,
        'avg_bedtime': format_time(avg_bedtime),
        'avg_wake_time': format_time(avg_wake),
        'consistency_score': consistency
    }

def get_sleep_by_day(sleep_records):
    day_totals = defaultdict(float)
    day_counts = defaultdict(int)

    for record in sleep_records:
        start = parse_date(record['start'])
        end = parse_date(record['end'])
        duration = (end - start).total_seconds() / 3600

        if 3 <= duration <= 12:
            day = start.weekday()
            day_totals[day] += duration
            day_counts[day] += 1

    result = []
    for day in range(7):
        if day_counts[day] > 0:
            result.append(round(day_totals[day] / day_counts[day], 1))
        else:
            result.append(0)

    return result

def get_heatmap_data(step_records):
    matrix = [[0.0] * 24 for _ in range(7)]
    counts = [[0] * 24 for _ in range(7)]

    for record in step_records:
        start = parse_date(record['start'])
        day = start.weekday()
        hour = start.hour
        matrix[day][hour] += record['value']
        counts[day][hour] += 1

    for day in range(7):
        for hour in range(24):
            if counts[day][hour] > 0:
                matrix[day][hour] = round(matrix[day][hour] / counts[day][hour], 2)

    max_val = max(val for row in matrix for val in row)
    if max_val > 0:
        for day in range(7):
            for hour in range(24):
                matrix[day][hour] = round(matrix[day][hour] / max_val, 3)

    return matrix

def detect_biphasic(sleep_records):
    day_sleeps = defaultdict(list)
    for record in sleep_records:
        start = parse_date(record['start'])
        end = parse_date(record['end'])
        duration = (end - start).total_seconds() / 3600
        if 0.25 <= duration <= 12:
            day_sleeps[start.date()].append(duration)

    if not day_sleeps:
        return False

    biphasic_days = sum(1 for sleeps in day_sleeps.values() if len(sleeps) >= 2)
    total_days = len(day_sleeps)

    return (biphasic_days / total_days) >= 0.30

def get_nap_metrics(sleep_records):
    nap_starts = []
    nap_durations = []

    day_sleeps = defaultdict(list)
    for record in sleep_records:
        start = parse_date(record['start'])
        end = parse_date(record['end'])
        duration = (end - start).total_seconds() / 3600
        if 0.25 <= duration <= 12:
            day_sleeps[start.date()].append({
                'start': start, 'end': end, 'duration': duration
            })

    for date, sleeps in day_sleeps.items():
        if len(sleeps) >= 2:
            sleeps.sort(key=lambda x: x['duration'])
            nap = sleeps[0]
            nap_starts.append(nap['start'].hour + nap['start'].minute / 60)
            nap_durations.append(nap['duration'])

    if not nap_starts:
        return {'avg_nap_time': 'No data', 'avg_nap_duration': 0}

    avg_nap_hour = sum(nap_starts) / len(nap_starts)
    avg_nap_dur = round(sum(nap_durations) / len(nap_durations) * 60)

    def format_time(decimal_hour):
        hour = int(decimal_hour) % 24
        minute = int((decimal_hour % 1) * 60)
        period = 'AM' if hour < 12 else 'PM'
        display_hour = hour if hour <= 12 else hour - 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour}:{minute:02d} {period}"

    return {
        'avg_nap_time': format_time(avg_nap_hour),
        'avg_nap_duration': avg_nap_dur
    }

def compute_all_metrics(sleep_records, step_records, heart_rate_records):
    distribution = get_activity_distribution(step_records)
    is_biphasic = detect_biphasic(sleep_records)

    # Suppress nap hours from the activity distribution so they
    # don't distort the peak detection for biphasic sleepers
    if is_biphasic:
        nap_data = get_nap_metrics(sleep_records)
        if nap_data['avg_nap_time'] != 'No data':
            try:
                parts = nap_data['avg_nap_time'].split(' ')
                nap_hour = int(parts[0].split(':')[0])
                period = parts[1]
                if period == 'PM' and nap_hour != 12:
                    nap_hour += 12
                elif period == 'AM' and nap_hour == 12:
                    nap_hour = 0
                distribution[nap_hour % 24] *= 0.3
                distribution[(nap_hour + 1) % 24] *= 0.3
            except Exception:
                pass

    peak_hour = get_peak_hours(distribution)
    crash_hour = get_crash_hour(distribution)
    sleep_metrics = get_sleep_metrics(sleep_records)

    def hour_to_time(hour):
        period = 'AM' if hour < 12 else 'PM'
        display = hour if hour <= 12 else hour - 12
        if display == 0:
            display = 12
        return f"{display}:00 {period}"

    low_confidence = len(sleep_records) < 14 or sleep_metrics['avg_duration'] == 0

    return {
        'activity_distribution': distribution,
        'peak_hour': peak_hour,
        'peak_window': f"{hour_to_time(peak_hour)} - {hour_to_time((peak_hour + 3) % 24)}",
        'crash_hour': crash_hour,
        'crash_window': f"{hour_to_time(crash_hour)} - {hour_to_time((crash_hour + 2) % 24)}",
        'avg_duration': sleep_metrics['avg_duration'],
        'avg_bedtime': sleep_metrics['avg_bedtime'],
        'avg_wake_time': sleep_metrics['avg_wake_time'],
        'consistency_score': sleep_metrics['consistency_score'],
        'sleep_record_count': len(sleep_records),
        'step_record_count': len(step_records),
        'low_confidence': low_confidence,
        'sleep_by_day': get_sleep_by_day(sleep_records),
        'heatmap_data': get_heatmap_data(step_records),
        'is_biphasic': is_biphasic,
        'nap_metrics': get_nap_metrics(sleep_records) if is_biphasic else {'avg_nap_time': 'No data', 'avg_nap_duration': 0}
    }