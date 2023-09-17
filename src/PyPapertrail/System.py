#!/usr/bin/env python3
"""
    File: System.py
"""
from typing import Optional
from datetime import datetime
try:
    from common import BASE_URL, __type_error__, convert_to_utc, requests_get, requests_put
    import common
    from Exceptions import SystemsError, InvalidServerResponse, ParameterError
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import BASE_URL, __type_error__, convert_to_utc, requests_get, requests_put
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import SystemsError, InvalidServerResponse, ParameterError

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
            Self = TypeVar("Self", bound="System")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)


class System(object):
    """Class to store a single system."""
################################
# Initialize:
################################
    def __init__(self,
                 api_key: str,
                 last_fetched: Optional[datetime] = None,
                 raw_system: Optional[dict] = None,
                 from_dict: Optional[dict] = None,
                 ) -> None:
        """
        Initialize a System object:
        :param api_key: Str: The api key.
        :param last_fetched: Optional[datetime]: The datetime object for when this was last fetched, note: must be set
            if using the raw_system parameter, and it will be ignored if using from_dict parameter.
        :param raw_system: Dict: The dict received from papertrail.
        :param from_dict: Dict: The dict created by __to_dict__().
        :raises: SystemsError: If raw_system and from_dict are either both None or both defined, or if an invalid
            raw_system dict, or from_dict dict are lacking a key.
        :raises: TypeError: If an invalid type is passed as a parameter.
        :returns: None
        """
        # Type checks:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif last_fetched is not None and not isinstance(last_fetched, datetime):
            __type_error__("last_fetched", "datetime", last_fetched)
        elif raw_system is not None and not isinstance(raw_system, dict):
            __type_error__("raw_system", "dict", raw_system)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)

        # Parameter checks:
        if raw_system is not None and last_fetched is None:
            error: str = "If using parameter raw_system, last_fetched must be defined."
            raise ParameterError(error)
        elif (raw_system is None and from_dict is None) and (raw_system is not None and from_dict is not None):
            error: str = "Either raw_system or from_dict must be defined, but not both."
            raise ParameterError(error)
        # Store the api key.
        self._api_key: str = api_key
        # Define the properties:
        self._id: int = -1
        self._name: str = ''
        self._last_event: Optional[datetime] = None
        self._auto_delete: bool = False
        self._json_info_link: str = ''
        self._html_info_link: str = ''
        self._search_link: str = ''
        self._ip_address: Optional[str] = None
        self._host_name: Optional[str] = None
        self._syslog_host_name: str = ''
        self._syslog_port: int = -1
        self._last_fetched: datetime = last_fetched
        # Load from raw_system, or from_dict:
        if raw_system is None and from_dict is None:
            error: str = "Either raw_system must be defined, but not both."
            raise SystemsError(error)
        elif raw_system is not None and from_dict is not None:
            error: str = "Either raw_system must be defined, but not both."
            raise SystemsError(error)
        elif raw_system is not None:
            self.__from_raw_system__(raw_system)
        else:
            self.__from_dict__(from_dict)
        return

##################################
# Load / Save functions:
##################################
    def __from_raw_system__(self, raw_system: dict) -> None:
        """
        Load from a raw system dict provided by papertrail.
        :param raw_system: Dict: The dict provided by Papertrail.
        :raises: SystemsError: When a key is not defined.
        :return: None
        """
        try:
            self._id = raw_system['id']
            self._name = raw_system['name']
            self._last_event = None
            if raw_system['last_event_at'] is not None:
                self._last_event = convert_to_utc(datetime.fromisoformat(raw_system['last_event_at'][:-1]))
            self._auto_delete = raw_system['auto_delete']
            self._json_info_link = raw_system['_links']['self']['href']
            self._html_info_link = raw_system['_links']['html']['href']
            self._search_link = raw_system['_links']['search']['href']
            self._ip_address = raw_system['ip_address']
            self._host_name = raw_system['hostname']
            self._syslog_host_name = raw_system['syslog']['hostname']
            self._syslog_port = raw_system['syslog']['port']
            self._last_fetched = convert_to_utc(datetime.utcnow())
        except (KeyError, ValueError) as e:
            error: str = "KeyError: %s. Maybe papertrail changed their response." % str(e)
            raise InvalidServerResponse(error, exception=e)
        return

    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict created by __to_dict__().
        :param from_dict: Dict: The dict to load from.
        :return: None
        """
        try:
            self._id = from_dict['id']
            self._name = from_dict['name']
            self._last_event = None
            if from_dict['last_event'] is not None:
                self._last_event = datetime.fromisoformat(from_dict['last_event'])
            self._auto_delete = from_dict['auto_delete']
            self._json_info_link = from_dict['json_link']
            self._html_info_link = from_dict['html_link']
            self._search_link = from_dict['search_link']
            self._ip_address = from_dict['ip_address']
            self._host_name = from_dict['host_name']
            self._syslog_host_name = from_dict['syslog_host']
            self._syslog_port = from_dict['syslog_port']
            self._last_fetched = None
            if from_dict['last_fetched'] is not None:
                self._last_fetched = datetime.fromisoformat(from_dict['last_fetched'])
        except (KeyError, ValueError) as e:
            error: str = "Invalid dict passed to __from_dict__"
            raise SystemsError(error, exception=e)
        return

    def __to_dict__(self) -> dict:
        """
        Create a JSON / Pickle friendly dict.
        :return: Dict.
        """
        return_dict = {
            'id': self._id,
            'name': self._name,
            'last_event': None,  # Dealt with later.
            'auto_delete': self._auto_delete,
            'json_link': self._json_info_link,
            'html_link': self._html_info_link,
            'search_link': self._search_link,
            'ip_address': self._ip_address,
            'host_name': self._host_name,
            'syslog_host': self._syslog_host_name,
            'syslog_port': self._syslog_port,
            'last_fetched': None,
        }
        if self._last_event is not None:
            return_dict['last_event'] = self._last_event.isoformat()
        if self._last_fetched is not None:
            return_dict['last_fetched'] = self._last_fetched.isoformat()
        return return_dict

#############################################
# Methods:
#############################################
    def reload(self) -> Self:
        """
        Reload data from papertrail.
        :return: System: The updated system instance.
        """
        # Build url and headers:
        info_url = self._json_info_link
        raw_system: dict = requests_get(url=info_url, api_key=self._api_key)
        self.__from_raw_system__(raw_system)
        # set last fetched:
        self._last_fetched = convert_to_utc(datetime.utcnow())
        return self

    def update(self,
               name: Optional[str] = None,
               ip_address: Optional[str] = None,
               host_name: Optional[str] = None,
               description: Optional[str] = None,
               auto_delete: Optional[bool] = None,
               ) -> Self:
        """
        Update this system.
        :param name: Optional[Str]: The friendly name of the system.
        :param ip_address: Optional[Str]: The ip address of the system.
        :param host_name: Optional[Str]: The host name of the system.
        :param description: Optional[Str]: The freeform description of the system.
        :param auto_delete: Optional[Bool]: Whether to automatically delete the system.
        :raises TypeError: If an invalid type is passed.
        :raises ValueError: If an invalid valid is passed.
        :raises InvalidServerResponse: If server sends bad JSON.
        :raises RequestReadTimeout: If the server fails to respond in time.
        :raises SystemsError:
            -> When nothing passed.
            -> When requests.RequestException occurs.
        :return: System: The updated system instance.
        """
        # Type / value / parameter checks:
        if name is not None and not isinstance(name, str):
            __type_error__("name", "str", name)
        elif ip_address is not None and not isinstance(ip_address, str):
            __type_error__("ip_address", "str", ip_address)
        elif host_name is not None and not isinstance("host_name", str):
            __type_error__("host_name", "str", host_name)
        elif description is not None and not isinstance(description, str):
            __type_error__("description", "str", description)
        elif auto_delete is not None and not isinstance(auto_delete, bool):
            __type_error__("auto_delete", "bool", auto_delete)
        all_none = True
        for parameter in (name, ip_address, host_name, description, auto_delete):
            if parameter is not None:
                all_none = False
        if all_none:
            error: str = "At least one parameter must be defined."
            raise ParameterError(error)
        # Build url and headers:
        update_url: str = BASE_URL + "systems/%i.json" % self._id
        # Build json data:
        json_data = {'system': {}}
        if name is not None:
            json_data['system']['name'] = name
        if ip_address is not None:
            json_data['system']['ip_address'] = ip_address
        if host_name is not None:
            json_data['system']['hostname'] = host_name
        if description is not None:
            json_data['system']['description'] = description
        if auto_delete is not None:
            json_data['system']['auto_delete'] = auto_delete
        # Make the PUT request:
        raw_system: dict = requests_put(url=update_url, api_key=self._api_key, json_data=json_data)
        # Reload from raw_system response, and set last fetched:
        self.__from_raw_system__(raw_system)
        self._last_fetched = convert_to_utc(datetime.utcnow())
        return self

#########################################
# Overrides:
#########################################
    def __eq__(self, other: Self | int | str) -> bool:
        """
        Equality test, tests system.id.
        :param other: System | int | str: The system to compare to, either a System object, an int for the system id, or
            a str for the system name.
        :return: Bool: True if ids are equal.
        """
        if isinstance(other, type(self)):
            return self._id == other._id
        elif isinstance(other, int):
            return self._id == other
        elif isinstance(other, str):
            return self._name == other
        raise TypeError("Cannot compare System to %s" % str(type(other)))

    def __str__(self) -> str:
        """
        Refer as a string, return name
        :return: Str
        """
        return self._name

    def __int__(self) -> int:
        """
        Refer as an int, return ID.
        :return: Int
        """
        return self._id

#########################################
# Properties:
#########################################
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
        System name.
        :return: Str
        """
        return self._name

    @property
    def last_event(self) -> Optional[datetime]:
        """
        Last event date / time.
        :return: Optional timezone-aware datetime object.
        """
        return self._last_event

    @property
    def auto_delete(self) -> bool:
        """
        Auto delete.
        NOTE: I'm not sure what this means, because it's not in the web docs.
        :return: Bool.
        """
        return self._auto_delete

    @property
    def json_info_link(self) -> str:
        """
        Link to json information.
        :return: Str
        """
        return self._json_info_link

    @property
    def html_info_link(self) -> str:
        """
        Link to HTML information.
        :return: Str
        """
        return self._html_info_link

    @property
    def search_link(self) -> str:
        """
        Link to search the logs of this system.
        :return: Str
        """
        return self._search_link

    @property
    def ip_address(self) -> Optional[str]:
        """
        The IP address of the system.
        :return: Optional[str]
        """
        return self._ip_address

    @property
    def host_name(self) -> Optional[str]:
        """
        The host name of this system.
        :return: Optional[str]
        """
        return self._host_name

    @property
    def syslog_host_name(self) -> str:
        """
        Syslog target host name.
        :return: Str
        """
        return self._syslog_host_name

    @property
    def syslog_port(self) -> int:
        """
        Syslog target port
        :return: Int
        """
        return self._syslog_port

    @property
    def last_fetched(self) -> datetime:
        """
        Date/Time this system was last fetched from papertrail.
        :return: Timezone-aware datetime object.
        """
        return self._last_fetched
