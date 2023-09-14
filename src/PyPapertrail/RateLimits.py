#!/usr/bin/env python3
"""
    File: RateLimits.py
"""
from typing import Optional

# Defaults taken from: https://www.papertrail.com/help/http-api/
limit: int = 25
remaining: int = limit
reset: int = 5


class RateLimits(object):
    """Class to hold rate limit properties."""
#######################
# Initialize:
#######################
    def __init__(self) -> None:
        """
        Initialize rate limits.
        """
        return

######################
# Properties:
######################
    @property
    def limit(self) -> Optional[int]:
        """
        The total number of requests allowed during the rate limit window, currently 25.
        :return: Optional[int]
        """
        global limit
        return limit

    @property
    def remaining(self) -> Optional[int]:
        """
         The number of requests not yet used within the current rate limit window.
        :return: Optional[int]
        """
        global remaining
        return remaining

    @property
    def reset(self) -> Optional[int]:
        """
        The duration (in seconds) remaining until the rate limit window resets, currently 5 seconds.
        :return: Optional[int]
        """
        global reset
        return reset

#
# ########################################################################################################################
# # TEST CODE:
# ########################################################################################################################
# if __name__ == '__main__':
#     from apiKey import API_KEY
#
#     exit(0)
