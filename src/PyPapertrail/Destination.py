#!/usr/bin/env python3
"""
    File: Destination.py
"""
from typing import Optional
from datetime import datetime
try:
    from common import BASE_URL, __type_error__, convert_to_utc, requests_get
    import common
    from Exceptions import DestinationError, ParameterError, InvalidServerResponse
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import BASE_URL, __type_error__, convert_to_utc, requests_get
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import DestinationError, ParameterError, InvalidServerResponse

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
            Self = TypeVar("Self", bound="Destination")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)


class Destination(object):
    """
    Class storing a single log destination.
    """
##############################################
# Initialize:
##############################################
    def __init__(self,
                 api_key: str,
                 raw_destination: Optional[dict] = None,
                 from_dict: Optional[dict] = None,
                 last_fetched: Optional[datetime] = None,
                 ) -> None:
        """
        Initialize a single destination.
        :param api_key: Str: Api key for papertrail.
        :param raw_destination: Dict: The raw response dict from papertrail.
            Note: If using raw_destination, last_fetched must be defined.
        :param from_dict: Dict: The dict created by __to_dict__().
        :param last_fetched: Datetime object: The date and time this was last fetched from the server.
        :return: None
        """
        # Type checks:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif raw_destination is not None and not isinstance(raw_destination, dict):
            __type_error__("raw_destination", "dict", raw_destination)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        elif last_fetched is not None and not isinstance(last_fetched, datetime):
            __type_error__("last_fetched", "datetime", last_fetched)

        # Parameter checks:
        if (raw_destination is None and from_dict is None) or (raw_destination is not None and from_dict is not None):
            error: str = "ParameterError: Either raw_destination or from_dict must be defined, but not both."
            raise ParameterError(error)
        elif raw_destination is not None and last_fetched is None:
            error: str = "ParameterError: If using raw_destination you must use last_fetched."
            raise ParameterError(error)

        # Store api key, and last fetched:
        self._api_key: str = api_key
        self._last_fetched: Optional[datetime] = None
        if last_fetched is not None:
            self._last_fetched = convert_to_utc(last_fetched)

        # Initialize properties.
        self._id: int = -1
        self._filter: Optional[str] = None
        self._syslog_host_name: str = ''
        self._syslog_port: int = -1
        self._description: str = ''
        self._info_link: str = ''

        # Load this instance:
        if raw_destination is not None:
            self.__from_raw_log_destination__(raw_destination)
        elif from_dict is not None:
            self.__from_dict__(from_dict)

        # Check port for port # 514, which is special. I'm assuming that Papertrail should never give this to us.
        if self._syslog_port == 514:
            raise DestinationError("port should never be 514.")
        return

##################################
# Load / Save functions:
##################################
    def __from_raw_log_destination__(self, raw_destination) -> None:
        """
        Load from raw destination response from papertrail.
        :param raw_destination: Dict: dict received from papertrail.
        :return: None
        """
        try:
            self._id = raw_destination['id']
            self._filter = raw_destination['filter']
            self._syslog_host_name = raw_destination['syslog']['hostname']
            self._syslog_port = raw_destination['syslog']['port']
            self._description = raw_destination['syslog']['description']
            self._info_link = BASE_URL + 'destinations/%i.json' % self._id
        except KeyError as e:
            error: str = "Key not found, perhaps papertrail changed their response."
            raise InvalidServerResponse(error, exception=e)
        return

    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict provided by __to_dict__().
        :param from_dict: Dict: The dict to load from.
        :return: None
        """
        try:
            self._id = from_dict['id']
            self._filter = from_dict['filter']
            self._syslog_host_name = from_dict['host_name']
            self._syslog_port = from_dict['port']
            self._description = from_dict['description']
            self._info_link = from_dict['info_link']
            self._last_fetched = None
            if from_dict['last_fetched'] is not None:
                self._last_fetched = datetime.fromisoformat(from_dict['last_fetched'])
        except (KeyError, ValueError) as e:
            error: str = "Invalid dict passed to __from_dict__()"
            raise DestinationError(error, exception=e)
        return

    def __to_dict__(self) -> dict:
        """
        Create a JSON / Pickle friendly dict of this instance.
        :return: Dict.
        """
        return_dict: dict = {
            'id': self._id,
            'filter': self._filter,
            'host_name': self._syslog_host_name,
            'port': self._syslog_port,
            'description': self._description,
            'info_link': self._info_link,
            'last_fetched': None,
        }
        if self._last_fetched is not None:
            return_dict['last_fetched'] = self._last_fetched.isoformat()
        return return_dict

###########################
# Methods:
###########################
    def reload(self) -> Self:
        """
        Reload this destination from the server.
        :return: Destination: This instance.
        """
        # Build url:
        reload_url = BASE_URL + 'destinations/%i.json' % self._id
        # Make request:
        response: dict = requests_get(url=reload_url, api_key=self._api_key)
        # Parse response data:
        self.__from_raw_log_destination__(response)
        # Update last fetched:
        self._last_fetched = convert_to_utc(datetime.utcnow())
        return self

###########################
# Overrides:
###########################
    def __eq__(self, other: Self | int | str) -> bool:
        """
        Equality check, of other is Destination object, it compares id, if other is an int, it compares syslog port,
        otherwise if other is a str it compares syslog host name.
        :param other: Destination | int | str: The object to compare to.
        :return: Bool.
        """
        if isinstance(other, type(self)):
            return self._id == other._id
        elif isinstance(other, int):
            return self._syslog_port == other
        elif isinstance(other, str):
            return self._syslog_host_name == other
        error: str = "Cannot compare Destination object to %s" % str(type(other))
        raise TypeError(error)

    def __str__(self) -> str:
        """
        Referring as a string returns the syslog host name.
        :return: Str: The syslog host name.
        """
        return self._syslog_host_name

    def __int__(self) -> int:
        """
        Referring as an int returns the syslog port.
        :return: Int: The syslog port.
        """
        return self._syslog_port

###########################
# Properties:
###########################
    @property
    def id(self) -> int:
        """
        Papertrail ID
        :return: Int
        """
        return self._id

    @property
    def filter(self) -> str:
        """
        Filters for this destination.
        :return: Str
        """
        return self._filter

    @property
    def syslog_host_name(self) -> str:
        """
        Syslog target host name
        :return: Str
        """
        return self._syslog_host_name

    @property
    def syslog_port(self) -> int:
        """
        Syslog target port.
        :return: Int
        """
        return self._syslog_port

    @property
    def description(self) -> str:
        """
        Destination description.
        :return: Str
        """
        return self._description

    @property
    def info_link(self) -> str:
        """
        Link to json info.
        :return: Str
        """
        return self._info_link

    @property
    def last_fetched(self) -> datetime:
        """
        Last time this was loaded from the server.
        :return: Datetime: None if not loaded.
        """
        return self._last_fetched
