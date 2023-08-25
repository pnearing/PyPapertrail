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
from Group import Group



class Groups(object):
    """Class to represent all the groups."""
    _GROUPS: list[Group] = []
    _IS_LOADED: bool = False
    _LAST_FETCHED: Optional[datetime] = None

###################################
# Initialize:
###################################
    def __init__(self, api_key: str, from_dict: Optional[dict] = None, do_load: bool = True):
        """
        Initialize all the groups, loading from papertrail if requested.
        :param api_key: Str: The api key.
        :param from_dict: Optional[dict]: The dict created by __to_dict__(); Note: that if from_dict is not None, then
            the do_load option is ignored. Default = None
        :param do_load: Bool: Load from Papertrail, True = Load, False = Don't load. Default = True.
        """
        # Type checks:
        if not isinstance(api_key, str):
            __type_error__("api_key","str", api_key)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        elif not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)
        # Store api_key:
        self._api_key = api_key
        # Load the groups:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif do_load:
            self.load()
        return

########################################
# To / From dict methods:
########################################
    def __from_dict__(self, from_dict: dict):
        """
        Load from a dict created by __to_dict__()
        :param from_dict: Dict: The dict provided by __to_dict__().
        :return: Dict.
        """
        pass

    def __to_dict__(self) -> dict:
        """
        Store this list of groups as a json / pickle friendly dict.
        :return: Dict
        """
        pass

#########################
# Load:
#########################
    def load(self) -> Self:
        """
        Load from papertrail.
        :return: Self.
        """
        # Build url and make request:
        list_url = BASE_URL + "groups.json"
        raw_groups: list[dict] = requests_get(url=list_url, api_key=self._api_key)
        # Parse the response from papertrail:
        for raw_group in raw_groups:
            group = Group(api_key=self._api_key, raw_group=raw_group)
            self._GROUPS.append(group)
        self._IS_LOADED = True
        self._LAST_FETCHED = datetime.utcnow().replace(tzinfo=timezone.utc)
        return self
