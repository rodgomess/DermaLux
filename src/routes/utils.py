from datetime import datetime, timedelta, timezone

def convert_unix_epoch(unix_epoch):
        brasilia = timezone(timedelta(hours=-3))
        return datetime.fromtimestamp(unix_epoch / 1000, tz=brasilia)