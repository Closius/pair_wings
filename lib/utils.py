import datetime
import threading
import logging
import os


DATA_FORMAT = '%d.%m.%Y %H:%M:%S,%f'


def percentage(percent, whole):
    return (percent * whole) / 100.0


def position_side(side):
    return 1 if side == "LONG" else -1


def error_percent(experiment, theory):
    """

    theory > experiment = negative

    :param experiment:
    :param theory:
    :return:
    """
    error = (abs(experiment - theory) / theory) * 100
    if theory > experiment:
        return - abs(error)
    else:
        return abs(error)


def get_precision(value):
    try:
        return len(str(value).split(".")[1])
    except:
        return 0


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


def setup_logger(name, log_file, level=logging.INFO, stream=False):
    if os.path.exists(log_file):
        os.remove(log_file)
    formatter_file = logging.Formatter('%(asctime)s|%(thread)d: %(message)s')
    formatter_main = logging.Formatter('%(asctime)s|%(thread)d %(name)s: %(message)s')
    handler_f = logging.FileHandler(log_file)
    handler_s = logging.StreamHandler()
    handler_f.setFormatter(formatter_file)
    handler_s.setFormatter(formatter_main)
    if name == "":
        logger = logging.getLogger()
    else:
        logger = logging.getLogger(name)
        logging.getLogger().info(f" {name} --> {threading.get_ident()} thread")
    logger.addHandler(handler_f)
    if stream:
        logger.addHandler(handler_s)
    logger.setLevel(level)
    logger.propagate = False

    return logger


