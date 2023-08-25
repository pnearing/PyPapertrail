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
from Exceptions import DestinationError, RequestReadTimeout, InvalidServerResponse


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
                 ) -> None:
        """
        Initialize a single destination.
        :param api_key: Str: Api key for papertrail.
        :param raw_destination: Dict: The raw response dict from papertrail.
        :param from_dict: Dict: The dict created by __to_dict__().
        :return: None
        """
        # Type checks:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif raw_destination is not None and not isinstance(raw_destination, dict):
            __type_error__("raw_destination", "dict", raw_destination)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        # Store api key:
        self._api_key: str = api_key
        # Initialize properties.
        self._id: int = -1
        self._filter: Optional[str] = None
        self._host_name: str = ''
        self._port: int = -1
        self._description: str = ''
        self._info_link: str = ''
        if raw_destination is None and from_dict is None:
            error: str = "Either raw_destination or from_dict must be defined, but not both."
            raise DestinationError(error)
        elif raw_destination is not None and from_dict is not None:
            error: str = "Either raw_destination or from_dict must be defined, but not both."
            raise DestinationError(error)
        elif raw_destination is not None:
            self.__from_raw_log_destination__(raw_destination)
        else:
            self.__from_dict__(from_dict)
        # Check port for port # 514, which is special. I'm assuming that Papertrail should never give this to us.
        if self._port == 514:
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
        self._id = raw_destination['id']
        self._filter = raw_destination['filter']
        self._host_name = raw_destination['syslog']['hostname']
        self._port = raw_destination['syslog']['port']
        self._description = raw_destination['syslog']['description']
        self._info_link = BASE_URL + 'destinations/%i.json' % self._id
        return

    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict provided by __to_dict__().
        :param from_dict: Dict: The dict to load from.
        :return: None
        """
        self._id = from_dict['id']
        self._filter = from_dict['filter']
        self._host_name = from_dict['host_name']
        self._port = from_dict['port']
        self._description = from_dict['description']
        self._info_link = from_dict['info_link']
        return

    def __to_dict__(self) -> dict:
        """
        Create a JSON / Pickle friendly dict of this instance.
        :return: Dict.
        """
        return_dict: dict = {
            'id': self._id,
            'filter': self._filter,
            'host_name': self._host_name,
            'port': self._port,
            'description': self._description,
            'info_link': self._info_link,
        }
        return return_dict

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
    def host_name(self) -> str:
        """
        Syslog target host name
        :return: Str
        """
        return self._host_name

    @property
    def port(self) -> int:
        """
        Syslog target port.
        :return: Int
        """
        return self._port

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