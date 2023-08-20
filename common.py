#!/usr/bin/env python3
"""
Common variables / functions for papertrail api.
"""
from typing import Any, NoReturn
from datetime import datetime

BASE_URL: str = 'https://papertrailapp.com/api/v1/'


def is_timezone_aware(dt: datetime) -> bool:
    """
    Checks if a given datetime object is timezone-aware.
    :param dt: The datetime object to check.
    :return: Bool, True if timezone-aware, False if timezone-unaware.
    """
    #
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def __type_error__(desired_types: str, received_obj: Any) -> NoReturn:
    """
    Raise a TypeError with a good message.
    :param desired_types: Str: String of desired type(s).
    :param received_obj: The var which was received, note: type() will be called on it.
    :return: NoReturn
    """
    error: str = "TypeError: got %s type, expected: %s" % (str(type(received_obj)), desired_types)
    raise TypeError(error)
