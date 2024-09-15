import datetime

DATA_FORMAT = '%d.%m.%Y %H:%M:%S,%f'


def ts_to_datetime(timestamp: int):
    """
    :param timestamp: in milliseconds
    """
    return datetime.datetime.fromtimestamp(timestamp / 1000)


def ts_to_text(timestamp: int):
    """
    :param timestamp: in milliseconds
    """
    return ts_to_datetime(timestamp).strftime(DATA_FORMAT)


def datetime_text_to_ts(dt_text: str):
    """

    :param dt_text: see DATA_FORMAT
    :return: timestamp im milliseconds
    """
    dt_obj = datetime.datetime.strptime(dt_text, DATA_FORMAT)
    return dt_obj.timestamp() * 1000
