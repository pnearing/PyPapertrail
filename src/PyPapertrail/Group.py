#!/usr/bin/env python3
"""
    File: Group.py
"""
from typing import Optional, Iterator
from datetime import datetime
import pytz
from warnings import warn
try:
    from common import BASE_URL, __type_error__, convert_to_utc, requests_get, requests_put, requests_post
    import common
    from Exceptions import GroupError, PapertrailWarning, InvalidServerResponse, ParameterError
    from System import System
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import BASE_URL, __type_error__, convert_to_utc, requests_get, requests_put, requests_post
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import GroupError, PapertrailWarning, InvalidServerResponse, ParameterError
    from PyPapertrail.System import System

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
            Self = TypeVar("Self", bound="Group")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)


class Group(object):
    """Class to store a single group."""
#############################
# Initialize:
#############################
    def __init__(self,
                 api_key: str,
                 raw_group: Optional[dict] = None,
                 from_dict: Optional[dict] = None,
                 last_fetched: Optional[datetime] = None,
                 ) -> None:
        """
        Initialize this group:
        :param api_key: Str: Api key.
        :param last_fetched: Datetime object: Datetime last fetched (UTC).
        :param raw_group: Dict: The dict provided by papertrail.
        :param from_dict: Dict: A dict created by __to_dict__().
        """
        # Type checks:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif last_fetched is not None and not isinstance(last_fetched, datetime):
            __type_error__("last_fetched", "datetime", last_fetched)
        elif raw_group is not None and not isinstance(raw_group, dict):
            __type_error__("raw_group", "dict", raw_group)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)

        # Parameter checks:
        if (raw_group is None and from_dict is None) or (raw_group is not None and from_dict is not None):
            error: str = "ParameterError: Either raw_group or from_dict must be defined, but not both."
            raise ParameterError(error)
        elif raw_group is not None and last_fetched is None:
            error: str = "ParameterError: If using raw_group, last_fetched must be defined."
            raise ParameterError(error)

        # Store api_key and last_fetched:
        self._api_key: str = api_key
        self._last_fetched: Optional[datetime] = None
        if last_fetched is not None:
            self._last_fetched = convert_to_utc(last_fetched)

        # Set properties:
        self._name: str = ''
        self._id: int = -1
        self._system_wildcard: Optional[str] = None
        self._self_link: str = ''
        self._html_link: str = ''
        self._search_link: str = ''
        self._systems: list[System] = []

        # Load this instance:
        if raw_group is not None:
            self.__from_raw_group__(raw_group)
        elif from_dict is not None:
            self.__from_dict__(from_dict)
        return

##########################################
# Load / save functions:
##########################################
    def __from_raw_group__(self, raw_group: dict) -> None:
        """
        Load from raw group dict provided by papertrail.
        :param raw_group: Dict: The dict provided by papertrail.
        :return: None
        """
        # Null Check SYSTEMS:
        if common.SYSTEMS is None:
            error = "Systems not loaded."
            raise GroupError(error)
        try:
            self._id = raw_group['id']
            self._name = raw_group['name']
            self._system_wildcard = raw_group['system_wildcard']
            self._self_link = raw_group['_links']['self']['href']
            self._html_link = raw_group['_links']['html']['href']
            self._search_link = raw_group['_links']['search']['href']
            self._systems = []
            for raw_system in raw_group['systems']:
                system_found: bool = False
                for system in common.SYSTEMS:
                    if system.id == raw_system['id']:
                        self._systems.append(system)
                        system_found = True
                if not system_found:
                    error: str = "System not found."
                    raise IndexError(error)
        except KeyError as e:
            error: str = "Key not found, perhaps papertrail changed their response."
            raise InvalidServerResponse(error, exception=e)
        return

    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict provided by __to_dict__().
        :param from_dict: Dict: The dict provided by __to_dict_().
        :return: None
        """
        # Null check SYSTEMS:
        if common.SYSTEMS is None:
            error: str = "Systems not loaded."
            raise GroupError(error)
        try:
            self._id = from_dict['id']
            self._name = from_dict['name']
            self._system_wildcard = from_dict['wildcard']
            self._self_link = from_dict['self_link']
            self._html_link = from_dict['html_link']
            self._search_link = from_dict['search_link']
            self._last_fetched = None
            if from_dict['last_fetched'] is not None:
                self._last_fetched = datetime.fromisoformat(from_dict['last_fetched'])
            for sys_id in from_dict['system_ids']:
                system_found: bool = False
                for system in common.SYSTEMS:
                    if system.id == sys_id:
                        self._systems.append(system)
                        system_found = True
                if not system_found:
                    error: str = "System not found."
                    raise IndexError(error)
        except (KeyError, ValueError) as e:
            error: str = "Invalid dict passed to __from_dict__()"
            raise GroupError(error, exception=e)
        return

    def __to_dict__(self) -> dict:
        """
        Return a JSON / Pickle friendly dict for this instance.
        :return: Dict.
        """
        return_dict: dict = {
            'id': self._id,
            'name': self._name,
            'wildcard': self._system_wildcard,
            'self_link': self._self_link,
            'html_link': self._html_link,
            'search_link': self._search_link,
            'last_fetched': None,
            'system_ids': []
        }
        if self._last_fetched is not None:
            return_dict['last_fetched'] = self._last_fetched.isoformat()
        for system in self._systems:
            return_dict['system_ids'].append(system.id)
        return return_dict

###############################
# Methods:
###############################
    def add_system(self, sys_to_add: System | int | str) -> Self:
        """
        Add a given system to this group.
        :param sys_to_add: System | int | str: The System to add if a System object, the system ID to add if an int, or
            the system name if a str.
        :raises IndexError: If System | int: ID | str: Name not found in Systems.
        :raises GroupError: If the system is already in the group.
        :return: Self.
            The updated group.
        """
        # global _SYSTEMS
        # Type check:
        if not isinstance(sys_to_add, (System, int, str)):
            __type_error__("sys_to_add", "System | int| str", sys_to_add)
        # Null check SYSTEMS:
        if common.SYSTEMS is None:
            error: str = "Systems not loaded."
            raise GroupError(error)

        # Get system_obj:
        system_obj: Optional[System] = None
        if isinstance(sys_to_add, System):
            if sys_to_add not in common.SYSTEMS:
                error: str = "System not found."
                raise IndexError(error)
            system_obj = sys_to_add
        elif isinstance(sys_to_add, int):
            system_found: bool = False
            for system in common.SYSTEMS:
                if system.id == sys_to_add:
                    system_obj = system
                    system_found = True
                    break
            if not system_found:
                error: str = "System ID: '%i' not found." % sys_to_add
                raise IndexError(error)
        else:  # sys_to_add is a str:
            system_found: bool = False
            for system in common.SYSTEMS:
                if system.name == sys_to_add:
                    system_obj = system
                    system_found = True
                    break
            if not system_found:
                error = "System Name: '%s' not found." % sys_to_add
                raise IndexError(error)
        # Check if system_obj in the group already:
        if system_obj in self._systems:
            error: str = "System already in group."
            raise GroupError(error)
        # Build url:
        join_url = BASE_URL + 'systems/%i/join.json' % system_obj.id
        # Build json data:
        json_data: dict = {"group_id": self._id}
        # Make the POST request:
        response: dict = requests_post(url=join_url, api_key=self._api_key, json_data=json_data)
        # Parse the response:
        try:
            if response['message'] != 'System updated':
                error: str = "Unexpected response message: %s" % response['message']
                raise InvalidServerResponse(error, url=join_url)
        except KeyError:
            error: str = "KeyError while parsing response."
            raise InvalidServerResponse(error, url=join_url)
        self.reload()
        return self

    def remove_system(self, sys_to_del: System | int | str) -> Self:
        """
        Remove a given system from this group.
        :param sys_to_del: System | int | str: If sys_to_del is a System, it's the system to delete, if it's an int it's
            the system ID number, otherwise if it's a str, then it's the name of the system.
        :raises IndexError: If the system is not found in the system list.
        :raises GroupError: If the system is not found in the group system list.
        :return: None
        """
        # Type check:
        if not isinstance(sys_to_del, (System, str, int)):
            __type_error__("sys_to_del", "System | int | str", sys_to_del)
        # Null check SYSTEMS:
        if common.SYSTEMS is None:
            error: str = "Systems not loaded."
            raise GroupError(error)

        # Get the system_obj System 'object' to remove:
        system_obj: Optional[System] = None
        if isinstance(sys_to_del, System):
            if sys_to_del not in common.SYSTEMS:
                error: str = "System not in systems."
                raise IndexError(error)
            system_obj = sys_to_del
        elif isinstance(sys_to_del, int):
            system_found: bool = False
            for system in common.SYSTEMS:
                if system.id == sys_to_del:
                    system_obj = system
                    system_found = True
                    break
            if not system_found:
                error: str = "System ID: '%i' not found." % sys_to_del
                raise IndexError(error)
        else:  # sys_to_del is a str:
            system_found: bool = False
            for system in common.SYSTEMS:
                if system.name == sys_to_del:
                    system_obj = system
                    system_found = True
                    break
            if not system_found:
                error: str = "System Name: '%s' not found." % sys_to_del
                raise IndexError(error)

        # Check that the system is in the system list.
        if system_obj not in self._systems:
            error: str = "System not in group."
            raise GroupError(error)
        # Build leave url:
        leave_url: str = BASE_URL + 'systems/%i/leave.json' % system_obj.id
        # Build JSON data:
        json_data: dict = {'group_id': self._id}
        # Make request:
        response = requests_post(url=leave_url, api_key=self._api_key, json_data=json_data)
        # Parse response data:
        try:
            if response['message'] != 'System updated':
                error: str = "Unexpected response from server: '%s'." % response['message']
                raise InvalidServerResponse(error)
        except KeyError as e:
            error: str = "Key 'message' not found in server response."
            raise InvalidServerResponse(error, exception=e)
        # Remove the system from group systems:
        self._systems.remove(system_obj)
        return self

###############################
# Methods:
###############################
    def reload(self) -> Self:
        """
        Reload this group from papertrail.
        :return: Group.
        """
        # Use self link url and make request:
        raw_group: dict = requests_get(self._self_link, self._api_key)
        # Load from the raw group, and set last fetched:
        self.__from_raw_group__(raw_group)
        self._last_fetched = pytz.utc.localize(datetime.utcnow())
        return self

    def update(self,
               name: Optional[str] = None,
               system_wildcard: Optional[str] = None,
               ) -> Self:
        """
        Update a group.
        :param name: Optional[str]: The new name.
        :param system_wildcard: Optional[str]: The new system wildcard.
        :return: Group: The updated group.
        """
        # Type checks:
        if name is not None and not isinstance(name, str):
            __type_error__("name", "Optional[str]", name)
        elif system_wildcard is not None and not isinstance(system_wildcard, str):
            __type_error__("system_wildcard", "Optional[str]", system_wildcard)
        # Value checks:
        if name == self._name:
            warning: str = "Parameter name == self._name, setting parameter to None."
            warn(warning, PapertrailWarning)
        elif system_wildcard == self._system_wildcard:
            warning: str = "Parameter system_wildcard == self._system_wildcard, setting parameter to None."
            warn(warning, PapertrailWarning)
        # Parameter checks:
        if name is None and system_wildcard is None:
            error: str = "ParameterError: name and system_wildcard, can't both be None."
            raise ParameterError(error)
        # Get url:
        update_url: str = self._self_link
        # Build json data object:
        json_data: dict = {'group': {}}
        if name is not None:
            json_data['group']['name'] = name
        if system_wildcard is not None:
            json_data['group']['system_wildcard'] = system_wildcard
        # Make the put request:
        raw_group = requests_put(update_url, self._api_key, json_data)
        # Parse the response:
        self._last_fetched = convert_to_utc(datetime.utcnow())
        self.__from_raw_group__(raw_group)
        return self

###############################
# Overrides:
###############################
    def __eq__(self, other: Self | str | int) -> bool:
        """
        Equality check: If other is a Group, it checks the id, if other is a str, it checks the name, otherwise if
        other is an int, it checks id again.
        :param other: Group | str | int: The object to compare with.
        :return: Bool
        """
        if isinstance(other, type(self)):
            return self._id == other._id
        elif isinstance(other, str):
            return self._name == other
        elif isinstance(other, int):
            return self._id == other
        error: str = "Cannot compare Group with type %s" % str(type(other))
        raise TypeError(error)

    def __str__(self) -> str:
        """
        Referring to a group as a string returns the name of the group.
        :return: Str.
        """
        return self._name

    def __int__(self) -> int:
        """
        Referring to a group as an int return the id of the group.
        :return:
        """
        return self._id

    def __iter__(self) -> Iterator:
        """
        Getting an iterator gives you an iterator over the systems in the group.
        :return: Iterator
        """
        return iter(self._systems)

###############################
# Properties:
###############################
    @property
    def id(self) -> int:
        """
        Papertrail's system ID.
        :return: Int
        """
        return self._id

    @property
    def name(self) -> str:
        """
        Papertrail name.
        :return: Str
        """
        return self._name

    @property
    def system_wildcard(self) -> Optional[str]:
        """
        System inclusion wildcard.
        :return: Optional[str]
        """
        return self._system_wildcard

    @property
    def self_link(self) -> str:
        """
        Link to self url.
        :return: str
        """
        return self._self_link

    @property
    def html_link(self) -> str:
        """
        Link to HTML info.
        :return: Str
        """
        return self._html_link

    @property
    def search_link(self) -> str:
        """
        Link to search api
        :return: Str.
        """
        return self._search_link

    @property
    def last_fetched(self) -> datetime:
        """
        The last time this object was refreshed from the server.
        :return: Datetime object.
        """
        return self._last_fetched

    @property
    def systems(self) -> tuple[System]:
        """
        Return a tuple of the systems in this group.
        :return: Tuple[System]
        """
        return tuple(self._systems)
