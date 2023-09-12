#!/usr/bin/env python3
"""
    File: RateLimits.py
"""
from typing import Optional
from common import __type_error__
import common
# Version check:
common.__version_check__()
# # Define Self:
# try:
#     from typing import Self
# except ImportError:
#     try:
#         from typing_extensions import Self
#     except (ModuleNotFoundError, ImportError):
#         try:
#             from typing import TypeVar
#             Self = TypeVar("Self", bound="RateLimits")
#         except ImportError:
#             print("FATAL: Unable to define Self.")
#             exit(129)

limit: Optional[int] = None
remaining: Optional[int] = None
reset: Optional[int] = None


def parse_limit_header(headers: dict) -> None:
    """
    Parse the rate limit headers.
    :param headers: Dict: The headers.
    :raises IndexError | ValueError: If an invalid dict is passed.
    :return: None
    """
    # Pull in vars:
    global limit, remaining, reset
    # Type check:
    if not isinstance(headers, dict):
        __type_error__("headers", "dict", headers)
    limit = int(headers['X-Rate-Limit-Limit'])
    remaining = int(headers['X-Rate-Limit-Remaining'])
    reset = int(headers['X-Rate-Limit-Reset'])
    return


########################################################################################################################
# TEST CODE:
########################################################################################################################
if __name__ == '__main__':
    from apiKey import API_KEY

    exit(0)
