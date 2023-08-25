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
            Self = TypeVar("Self", bound="Group")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)
from typing import Optional
from datetime import datetime
import pytz
from common import __type_error__, convert_to_utc, requests_get
from Exceptions import GroupError


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
            raise GroupError(error)
        elif raw_group is not None and last_fetched is None:
            error: str = "ParameterError: If using raw_group, last_fetched must be defined."
            raise GroupError(error)

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
        try:
            self._id = raw_group['id']
            self._name = raw_group['name']
            self._system_wildcard = raw_group['system_wildcard']
            self._self_link = raw_group['_links']['self']['href']
            self._html_link = raw_group['_links']['html']['href']
            self._search_link = raw_group['_links']['search']['href']
        except KeyError as e:
            error: str "Key not found, perhaps papertrail changed their response."
            raise GroupError(error, exception=e)
        return

    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict provided by __to_dict__().
        :param from_dict: Dict: The dict provided by __to_dict_().
        :return: None
        """
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
        except KeyError as e:
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
        }
        if self._last_fetched is not None:
            return_dict['last_fetched'] = self._last_fetched.isoformat()
        return return_dict

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
        if isinstance(other, Self):
            return self._id == other._id
        elif isinstance(other, str):
            return self._name == other
        elif isinstance(other, int):
            return self._id == other
        error: str = "Cannot compare Group with %s" % str(type(other))
        raise GroupError(error)

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

###############################
# Methods:
###############################
    def reload(self) -> Self:
        """
        Reload this group from papertrail.
        :return: Group.
        """
        # Get url and make request:
        reload_url = self._self_link
        raw_group: dict = requests_get(reload_url, self._api_key)
        # Load from the raw group, and set last fetched:
        self.__from_raw_group__(raw_group)
        self._last_fetched = pytz.utc.localize(datetime.utcnow())
        return self

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
