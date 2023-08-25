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
from typing import Optional, Iterator
from datetime import datetime
import pytz
from common import BASE_URL, __type_error__, requests_get
from Exceptions import GroupError
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
    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict created by __to_dict__()
        :param from_dict: Dict: The dict provided by __to_dict__().
        :return: Dict.
        """
        try:
            self._LAST_FETCHED = None
            if from_dict['last_fetched'] is not None:
                self._LAST_FETCHED = datetime.fromisoformat(from_dict['last_fetched'])
            self._GROUPS = []
            for group_dict in from_dict['_groups']:
                group = Group(api_key=self._api_key, from_dict=group_dict)
                self._GROUPS.append(group)
        except KeyError as e:
            error: str = "Invalid dict passed to __from_dict__()"
            raise GroupError(error, exception=e)
        return

    def __to_dict__(self) -> dict:
        """
        Store this list of groups as a json / pickle friendly dict.
        :return: Dict
        """
        return_dict: dict = {
            'last_fetched': None,
            '_groups': [],
        }
        if self._LAST_FETCHED is not None:
            return_dict['last_fetched'] = self._LAST_FETCHED.isoformat()
        for group in self._GROUPS:
            group_dict = group.__to_dict__()
            return_dict['_groups'].append(group_dict)
        return return_dict

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
        self._LAST_FETCHED = pytz.utc.localize(datetime.utcnow())
        for raw_group in raw_groups:
            group = Group(api_key=self._api_key, raw_group=raw_group, last_fetched=self._LAST_FETCHED)
            self._GROUPS.append(group)
        self._IS_LOADED = True
        return self

#############################
# Overrides:
#############################
    def __getitem__(self, item: int | str | slice) -> Group | list[Group]:
        """
        Access this as a list / dict with an index.
        :param item: Int | str | slice: The index, if item is an int, index as a list, if item is a str, index by name,
            otherwise if index is a slice of type int, returns a list of groups as per the slice.
        :return: Group | list[Group]
        """
        if isinstance(item, int):
            return self._GROUPS[item]
        elif isinstance(item, str):
            for group in self._GROUPS:
                if group.name == item:
                    return group
            error: str = "Indexing as string, name '%s' not found." % item
            raise IndexError(error)
        elif isinstance(item, slice):
            error: str = "Can only slice Group by int."
            if not isinstance(item.start, int):
                raise ValueError(error)
            elif item.stop is not None and not isinstance(item.stop, int):
                raise ValueError(error)
            elif item.step is not None and not isinstance(item.step, int):
                raise ValueError(error)
            return self._GROUPS[item]
        error: str = "Can only index by Group, int, str, or slice with type int, not: %s" % str(type(item))
        raise TypeError(error)

    def __len__(self) -> int:
        """
        Return the number of groups.
        :return: Int
        """
        return len(self._GROUPS)

    def __iter__(self) -> Iterator:
        """
        Return an iterator of the groups.
        :return: Iterator
        """
        return iter(self._GROUPS)

##############################
# Properties:
##############################
    @property
    def is_loaded(self) -> bool:
        """
        Return if this has been loaded somehow.
        :return: Bool.
        """
        return self._IS_LOADED

    @property
    def last_fetched(self) -> datetime:
        """
        The date / time this was last retrieved from papertrail, time in UTC.
        :return: Datetime object.
        """
        return
########################################################################################################################
# TEST CODE:
########################################################################################################################
if __name__ == '__main__':
    from apiKey import API_KEY
    groups = Groups(api_key=API_KEY)

    groups[0].reload()
