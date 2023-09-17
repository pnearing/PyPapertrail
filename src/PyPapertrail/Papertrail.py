#!/usr/bin/env python3
"""
    File: Papertrail.py
"""
from typing import Optional
from urllib.parse import urlencode
from datetime import datetime
from warnings import warn
try:
    import common
    from common import BASE_URL, __type_error__, convert_to_utc, requests_get
    from Archives import Archives
    from Destinations import Destinations
    from Groups import Groups
    from Systems import Systems
    from Usage import Usage
    from Exceptions import PapertrailError, ParameterError, PapertrailWarning
    from Results import Results
    from System import System
    from Group import Group
    from Event import Event
    from RateLimits import RateLimits
except (ModuleNotFoundError, ImportError):
    import PyPapertrail.common as common
    from PyPapertrail.common import BASE_URL, __type_error__, convert_to_utc, requests_get
    from PyPapertrail.Archives import Archives
    from PyPapertrail.Destinations import Destinations
    from PyPapertrail.Groups import Groups
    from PyPapertrail.Systems import Systems
    from PyPapertrail.Usage import Usage
    from PyPapertrail.Exceptions import PapertrailError, ParameterError, PapertrailWarning
    from PyPapertrail.Results import Results
    from PyPapertrail.System import System
    from PyPapertrail.Group import Group
    from PyPapertrail.Event import Event
    from PyPapertrail.RateLimits import RateLimits

# Version check:
common.__version_check__()
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


class Papertrail(object):
    """
    Class for all papertrail objects.
    """
    def __init__(self,
                 api_key: str,
                 from_dict: Optional[dict] = None,
                 do_load: bool = True,
                 use_warnings: bool = True,
                 ) -> None:
        """
        Initialize papertrail interface.
        :param api_key: Str: The api key.
        :param from_dict: Dict: Load from a dict created by __to_dict__(), NOTE: if from_dict is used, do_load is
            ignored.
        :param do_load: Bool: Load from papertrail. Default = True.
        :param use_warnings: Bool: Use warnings. Default = True.
        :returns: None
        """
        # Type check:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        elif not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)
        elif not isinstance(use_warnings, bool):
            __type_error__("use_warnings", "bool", use_warnings)
        # Store use_warnings:
        common.USE_WARNINGS = use_warnings
        # Store api key:
        self._api_key = api_key
        # Define Papertrail objects:
        self._archives: Archives = Archives(api_key=api_key, from_dict=None, do_load=False)
        self._destinations: Destinations = Destinations(api_key=api_key, from_dict=None, do_load=False)
        self._systems: Systems = Systems(api_key=api_key, from_dict=None, do_load=False)
        self._groups: Groups = Groups(api_key=api_key, from_dict=None, do_load=False)
        self._usage: Usage = Usage(api_key=api_key, from_dict=None, do_load=False)
        self._rate_limits: RateLimits = RateLimits()

        # Load this instance:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif do_load:
            self._archives.load()
            self._destinations.load()
            self._systems.load()
            self._groups.load()
            self._usage.load()
            self.IS_LOADED = True
        return

####################################
# Load / Save:
####################################
    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict created by __to_dict__().
        :param from_dict:
        :return: None
        """
        try:
            self._archives.__from_dict__(from_dict['archives'])
            self._destinations.__from_dict__(from_dict['destinations'])
            self._systems.__from_dict__(from_dict['systems'])
            self._groups.__from_dict__(from_dict['groups'])
            self._usage.__from_dict__(from_dict['usage'])
            self.IS_LOADED = True
        except KeyError:
            error: str = "Invalid dict provided to __from_dict__()."
            raise PapertrailError(error)
        return

    def __to_dict__(self) -> dict:
        """
        Return a JSON / Pickle friendly dict.
        :return: Dict
        """
        return_dict: dict = {
            'archives': self._archives.__to_dict__(),
            'destinations': self._destinations.__to_dict__(),
            'groups': self._groups.__to_dict__(),
            'systems': self._systems.__to_dict__(),
            'usage': self._usage.__to_dict__(),
        }
        return return_dict

##################################
# Methods:
##################################
    def search(self,
               query: Optional[str] = None,
               system: Optional[System | str | int] = None,
               group: Optional[Group | str | int] = None,
               min_id: Optional[Event | int] = None,
               max_id: Optional[Event | int] = None,
               min_time: Optional[datetime] = None,
               max_time: Optional[datetime] = None,
               limit: Optional[int] = None,
               ) -> Results:
        """
        Search the logs:
        :param query: Optional[str]: The search query.
        :param system: Optional[System | str | int]: Limit search to this System object, system id if an int, system
            name if a str.
        :param group: Optional[Group | str | int]: Limit search to this Group object, group id if an int, or group
            name if a str.
        :param min_id: Optional[int | Event]: Min Event ID, or event, can't be combined with min_time.
        :param max_id: Optional[int | Event]: Max Event ID, or event, can't be combined with max_time.
        :param min_time: Optional[datetime]: The Min datetime object can't be combined with min_id.
        :param max_time: Optional[datetime]: The Max datetime can't be combined with max_id.
        :param limit: Optional[int]: Number of events to return.
        :raises TypeError: If an invalid type is passed.
        :raises ParameterError: If an invalid parameter combination is passed.
        :raises IndexError: If an invalid System id, name, or System object, an invalid Group id, name, Group object
            is passed.
        :return: Results object.
        """
        # Warn if needed:
        if common.USE_WARNINGS and not self._systems.is_loaded:
            warning: str = "Systems not loaded. Can't verify systems."
            warn(warning, PapertrailWarning)
        if common.USE_WARNINGS and not self._groups.is_loaded:
            warning: str = "Groups not loaded. Can't verify group."
            warn(warning, PapertrailWarning)

        # Type check:
        if query is not None and not isinstance(query, str):
            __type_error__("query", "Optional[str]", query)
        if system is not None and not isinstance(system, (Group, int, str)):
            __type_error__("system", "Optional[System | str | int]", system)
        if group is not None and not isinstance(group, (Group, int, str)):
            __type_error__("group", "Optional[Group | str | int", group)
        if min_id is not None and not isinstance(min_id, (int, Event)):
            __type_error__("min_id", "Optional[int | Event]", min_id)
        if max_id is not None and not isinstance(max_id, (int, Event)):
            __type_error__("max_id", "Optional[int | Event]", max_id)
        if min_time is not None and not isinstance(min_time, datetime):
            __type_error__("min_time", "Optional[datetime]", min_time)
        if max_time is not None and not isinstance(max_time, datetime):
            __type_error__("max_time", "Optional[datetime]", max_time)
        if limit is not None and not isinstance(limit, int):
            __type_error__("limit", "Optional[int]", limit)

        # Parameter check:
        if min_id is not None and min_time is not None:
            error: str = "Cannot use min_id and min_time at the same time."
            raise ParameterError(error)
        if max_id is not None and max_time is not None:
            error: str = "Cannot use max_id and max_time at the same time."
            raise ParameterError(error)

        # Build search parameters:
        search_params: dict = {}
        if query is not None:
            search_params['q'] = query
        if system is not None:
            if common.USE_WARNINGS and not self._systems.is_loaded:
                warning: str = "Systems not loaded, not verifying system input."
                warn(warning, PapertrailWarning)
            if isinstance(system, System):
                if self._systems.is_loaded and system not in self._systems:
                    error: str = "Provided System not in Systems."
                    raise IndexError(error)
                search_params['system_id'] = system.id
            else:
                if self._systems.is_loaded:
                    search_params['system_id'] = self._systems[system].id  # Raises IndexError if the system not found.
                else:  # Assume the input is correct:
                    search_params['system_id'] = system
        if group is not None:
            if common.USE_WARNINGS and not self._groups.is_loaded:
                warning: str = "Groups not loaded, not verifying group input."
                warn(warning, PapertrailWarning)
            if isinstance(group, Group):
                if self._groups.is_loaded and group not in self._groups:
                    error: str = "Provided group not in groups."
                    raise IndexError(error)
                search_params['group_id'] = group.id
            else:
                if self._groups.is_loaded:
                    search_params['group_id'] = self._groups[group].id  # Raises IndexError if the group not found.
                else:  # Assume the input is correct, but can only be an int.
                    if isinstance(group, int):
                        search_params['group_id'] = group
                    else:
                        error: str = "Groups not loaded, can't use str as group id. Abort."
                        TypeError(error)
        if min_id is not None:
            if isinstance(min_id, Event):
                search_params['min_id'] = min_id.id
            else:
                search_params['min_id'] = min_id
        if max_id is not None:
            if isinstance(max_id, Event):
                search_params['max_id'] = max_id.id
            else:
                search_params['max_id'] = max_id
        if min_time is not None:
            search_params['min_time'] = convert_to_utc(min_time).timestamp()
        if max_time is not None:
            search_params['max_time'] = convert_to_utc(max_time).timestamp()
        if limit is not None:
            search_params['limit'] = limit
        # Build search url:
        search_url = BASE_URL + "events/search.json"
        if len(search_params.keys()) != 0:
            search_url += '?'
            search_url += urlencode(search_params)
        # Make search request:
        raw_results = requests_get(url=search_url, api_key=self._api_key)
        # Parse results:
        search_results = Results(raw_results=raw_results)
        return search_results

##################################
# Properties:
##################################
    @property
    def archives(self) -> Archives:
        """
        Archives instance.
        :return: Archives
        """
        return self._archives

    @property
    def destinations(self) -> Destinations:
        """
        Destinations instance.
        :return: Destinations
        """
        return self._destinations

    @property
    def groups(self) -> Groups:
        """
        Groups instance.
        :return: Groups
        """
        return self._groups

    @property
    def systems(self) -> Systems:
        """
        Systems instance.
        :return: Systems
        """
        return self._systems

    @property
    def usage(self) -> Usage:
        """
        Usage instance.
        :return: Usage
        """
        return self._usage

    @property
    def rate_limits(self) -> RateLimits:
        """
        Rate Limits Instance.
        :return: RateLimits
        """
        return self._rate_limits


########################################################################################################################
# TEST CODE:
########################################################################################################################
if __name__ == '__main__':
    from apiKey import API_KEY
    papertrail = Papertrail(api_key=API_KEY, do_load=False)
    papertrail.systems.load()
    papertrail.groups.load()
    results = papertrail.search(query="ssh AND error")
    for event in results.events:
        print(event.message)

    exit(0)
