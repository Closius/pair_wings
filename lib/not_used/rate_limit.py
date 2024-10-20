"""
Rate limit public interface.

This module includes the wrapper for rate limit function invocations.

Usage:

self.http_private = RrateLimitSleepRetry(
                        HTTP(api_key=.., api_secret=.., demo=demo,),
                        calls=5, per_second=1)

# any function of self.http_private can be
#called not more than 5 calls per second
self.http_private.function()

"""

import inspect

import time
import threading
import logging


class RateLimitSleepRetry:
    def __init__(self, obj, function_names: list, calls=15, per_second=900):
        """
            Limit the number of calls of function_names. + Sleep, wait and Retry

            By default the function can't be called more than
            (15 calls every 15 minutes (900 seconds)).
        """
        self._rt_log = logging.getLogger()
        self._rt_clamped_calls = calls
        self._rt_period = per_second
        self._rt_obj = obj
        if not function_names:
            raise ValueError("function_names is empty: this will apply the rate limit to "
                         "ALL of the functions and get/set properties of the 'obj'. "
                         "Such behavior is not accepted. Please provide function names")
        self._function_names = function_names

        self._rt_last_reset = self._rt_clock()
        self._rt_num_calls = 0

        self._rt_lock = threading.RLock()

    def __getattribute__(self, item):
        if item.startswith("_"):
            return super().__getattribute__(item)
        elif item in self._function_names:
            with self._rt_lock:
                period_remaining = self._rt_period_remaining()

                # If the time window has elapsed then reset.
                if period_remaining <= 0:
                    self._rt_num_calls = 0
                    self._rt_last_reset = self._rt_clock()

                # Increase the number of attempts to call the function.
                self._rt_num_calls += 1

            # If the number of attempts to call the function exceeds the
            # maximum then raise an exception.
            if self._rt_num_calls > self._rt_clamped_calls:
                dept = 5
                st = [x.function for x in inspect.stack()[1:dept+1]]
                st.insert(0, item)
                s = "<-".join(st)
                self._rt_log.warning(f"Stock backend: too many calls. Rate limit: {self._rt_clamped_calls} "
                                             f"per {self._rt_period} seconds. Stack: '{s}<-...'")
                time.sleep(period_remaining)
            return getattr(self._rt_obj, item)

    def _rt_clock(self):
        if hasattr(time, 'monotonic'):
            return time.monotonic()
        return time.time()

    def _rt_period_remaining(self):
        elapsed = self._rt_clock() - self._rt_last_reset
        return self._rt_period - elapsed
