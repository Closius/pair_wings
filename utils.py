import datetime


def ts_to_datetime(timestamp: int):
    """

    :param timestamp: in milliseconds
    :return:
    """
    return datetime.datetime.fromtimestamp(timestamp / 1000)


def ts_to_text(timestamp: int):
    """

    :param timestamp: in milliseconds
    :return:
    """
    return ts_to_datetime(timestamp).strftime("%d/%m/%Y %H:%M:%S:%f")


def datetime_text_to_ts(dt_text: str):
    """
    to timestamp im milliseconds

    :param dt_text: '20.12.2016 09:38:42,76'
    :return:
    """
    dt_obj = datetime.datetime.strptime(dt_text,
                               '%d.%m.%Y %H:%M:%S,%f')
    return dt_obj.timestamp() * 1000
