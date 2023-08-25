#!/usr/bin/env python3
import sys
if sys.version_info.major != 3 or sys.version_info.minor < 10:
    print("Only python >= 3.10 supported")
    exit(128)
# Define Self:
try:
    from typing import Self
except ImportError:
    try:
        from typing_extensions import Self
    except (ModuleNotFoundError, ImportError):
        try:
            from typing import TypeVar
            Self = TypeVar("Self", bound="Groups")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)
from typing import Optional
from common import BASE_URL, __type_error__, requests_get
from Exceptions import GroupError
from datetime import datetime, timezone


class Group(object):
    """Class to store a single group."""
#############################
# Initialize:
#############################
    def __init__(self,
                 api_key: str,
                 raw_group: Optional[dict] = None,
                 from_dict: Optional[dict] = None):
        """
        Initialize a group:
        :param api_key: Str: The api key.
        :param raw_group: Optional[dict]: The dict provided by papertrail.
        :param from_dict: Optional[dict]: The dict provided by __to_dict__().
        """
        return

