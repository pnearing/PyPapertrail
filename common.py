#!/usr/bin/env python3
"""
Common variables / functions for papertrail api.
"""
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