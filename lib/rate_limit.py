"""
Rate limit public interface.

This module includes the decorator used to rate limit function invocations.

Usage:

# 30 calls per minute
CALLS = 30
RATE_LIMIT = 60

@rate_limit_sleep_retry(calls=CALLS, per_second=RATE_LIMIT)
def check_limit():
''' Empty function just to check for calls to API '''
return
"""

from functools import wraps

import time
import threading
import logging


class rate_limit_sleep_retry:
    def __init__(self, calls=15, per_second=900):
        """
            Limit the number of function's calls. + Sleep, wait and Retry

            By default the function can't be called more than
            (15 calls every 15 minutes (900 seconds)).
        """
        self.log = logging.getLogger(__name__)
        self.clamped_calls = calls
        self.period = per_second

        self.last_reset = self._clock()
        self.num_calls = 0

        self.lock = threading.RLock()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kargs):
            with self.lock:
                period_remaining = self.__period_remaining()

                # If the time window has elapsed then reset.
                if period_remaining <= 0:
                    self.num_calls = 0
                    self.last_reset = self._clock()

                # Increase the number of attempts to call the function.
                self.num_calls += 1

            # If the number of attempts to call the function exceeds the
            # maximum then raise an exception.
            if self.num_calls > self.clamped_calls:
                self.log.warning(f"Function '{func.__name__}' too many calls. Rate limit: {self.clamped_calls} "
                                             f"per {self.period} seconds")
                time.sleep(period_remaining)
            return func(*args, **kargs)

        return wrapper

    def _clock(self):
        if hasattr(time, 'monotonic'):
            return time.monotonic()
        return time.time()

    def __period_remaining(self):
        elapsed = self._clock() - self.last_reset
        return self.period - elapsed

