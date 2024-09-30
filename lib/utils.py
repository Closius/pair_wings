import datetime
import threading


DATA_FORMAT = '%d.%m.%Y %H:%M:%S,%f'


def ts_to_datetime(timestamp: int | str):
    """
    :param timestamp: in milliseconds
    """
    return datetime.datetime.fromtimestamp(int(timestamp) / 1000)


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


def datetime_to_ts(dt: datetime):
    return dt.strftime(DATA_FORMAT)


class Singleton(type):
    """
    Metaclass for creating a singleton class: preserve 1 singleton object in 1 thread
    Usage:
        class MyClass(BaseClass, metaclass=Singleton):
            pass
    """

    _instances = {}  # {"thread_id": {"cls": super().__call__} }

    def __call__(cls, *args, **kwargs):
        if threading.get_ident() not in cls._instances:
            cls._instances[threading.get_ident()] = {cls: super().__call__(*args, **kwargs)}
        else:
            if cls not in cls._instances[threading.get_ident()]:
                cls._instances[threading.get_ident()][cls] = super().__call__(*args, **kwargs)
        return cls._instances[threading.get_ident()][cls]
