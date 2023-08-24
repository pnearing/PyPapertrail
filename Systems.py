#!/usr/bin/env python3
from __future__ import annotations
from typing import Optional, Iterator, TypeVar
from datetime import datetime, timezone
from common import BASE_URL, __type_error__, requests_get, requests_post, requests_put
from Exceptions import SystemsError
from Destinations import Destination

Self = TypeVar("Self", bound="System")


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
        # Type / value / parameter checks:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif last_fetched is not None and not isinstance(last_fetched, datetime):
            __type_error__("last_fetched", "datetime", last_fetched)
        elif raw_system is not None and not isinstance(raw_system, dict):
            __type_error__("raw_system", "dict", raw_system)
        elif raw_system is not None and last_fetched is None:
            error: str = "If using parameter raw_system, last_fetched must be defined."
            raise SystemsError(error)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)

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
                self._last_event = datetime.fromisoformat(raw_system['last_event_at'][:-1])
                if raw_system['last_event_at'][-1].lower() == 'z':
                    self._last_event.replace(tzinfo=timezone.utc)
            self._auto_delete = raw_system['auto_delete']
            self._json_info_link = raw_system['_links']['self']['href']
            self._html_info_link = raw_system['_links']['html']['href']
            self._search_link = raw_system['_links']['search']['href']
            self._ip_address = raw_system['ip_address']
            self._host_name = raw_system['hostname']
            self._syslog_host_name = raw_system['syslog']['hostname']
            self._syslog_port = raw_system['syslog']['port']
            self._last_fetched = datetime.utcnow().replace(tzinfo=timezone.utc)
        except KeyError as e:
            error: str = "KeyError: %s. Maybe papertrail changed their response." % str(e)
            raise SystemsError(error, exception=e)
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
                self._last_fetched = datetime.fromisoformat(from_dict['last_fetched']).replace(tzinfo=timezone.utc)
        except KeyError as e:
            error: str = "KeyError while loading from_dict. Invalid data."
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
        self._last_fetched = datetime.utcnow().replace(tzinfo=timezone.utc)
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
            raise SystemsError(error)
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
        self._last_fetched = datetime.utcnow().replace(tzinfo=timezone.utc)
        return self
#########################################
# Overrides:
#########################################

    def __eq__(self, other: System) -> bool:
        """
        Equality test, tests system.id.
        :param other: System: The system to compare to.
        :return: Bool: True if ids are equal.
        """
        return self._id == other._id
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
########################################################################################################################
########################################################################################################################


class Systems(object):
    """Class to store the systems as a list."""
    _SYSTEMS: list[System] = []
    _IS_LOADED: bool = False
    _LAST_FETCHED: Optional[datetime] = None

###############################
# Initialize:
###############################
    def __init__(self,
                 api_key: str,
                 from_dict: Optional[dict] = None,
                 do_load: bool = True,
                 ) -> None:
        """
        Initialize the systems list.
        :param api_key: Str: The api key.
        :param from_dict: Dict: The dict to load from created by __to_dict__(), Note if not None do_load is ignored.
        :param do_load: Bool: True, make request from papertrail, False do not.
        :raises: SystemsError: On request error, or if invalid JSON is returned.
        """
        # Type Checks:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        elif not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)
        # store api key:
        self._api_key: str = api_key
        # Load Systems:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif do_load:
            self.load()
        return

##############################################
# Loading / saving functions:
##############################################
    def __to_dict__(self) -> dict:
        """
        Create a json / pickle friendly dict.
        :return: Dict.
        """
        return_dict: dict = {
            'last_fetched': None,
            '_systems': [],
        }
        if self._LAST_FETCHED is not None:
            return_dict['last_fetched'] = self._LAST_FETCHED.isoformat()
        for system in self._SYSTEMS:
            return_dict['_systems'].append(system.__to_dict__())
        return return_dict

    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from dict created by __to_dict__()
        :param from_dict: The dict
        :return: None
        """
        self._LAST_FETCHED = None
        if from_dict['last_fetched'] is not None:
            self._last_fetched = datetime.fromisoformat(from_dict['last_fetched']).replace(tzinfo=timezone.utc)
        self._SYSTEMS = []
        for system_dict in from_dict['_systems']:
            system = System(self._api_key, from_dict=system_dict)
            self._SYSTEMS.append(system)
        self._IS_LOADED = True
        return

###############################
# Methods:
###############################
    def load(self) -> None:
        # Set url and headers:
        list_url = BASE_URL + 'systems.json'
        system_list: list[dict] = requests_get(url=list_url, api_key=self._api_key)
        # Set last fetched time to NOW.
        self._LAST_FETCHED = datetime.utcnow().replace(tzinfo=timezone.utc)
        # Create SYSTEMS list:
        for raw_system in system_list:
            system = System(api_key=self._api_key, last_fetched=self._LAST_FETCHED, raw_system=raw_system)
            self._SYSTEMS.append(system)
        self._IS_LOADED = True
        return

    def register(self,
                 name: str,
                 host_name: Optional[str] = None,
                 ip_address: Optional[str] = None,
                 destination_port: Optional[int] = None,
                 destination_id: Optional[int] = None,
                 destination: Optional[Destination] = None,
                 description: Optional[str] = None,
                 auto_delete: Optional[bool] = None,
                 ) -> System:
        """
        Register a new system with papertrail.
        :param name: Str: Papertrail name.
        :param host_name: Optional[str]: Filter events to only those from this syslog host name.
        :param ip_address: Optional[str]: The Ip address of the system, it should be a static public ip.
        :param destination_port: Int: Syslog target port. If set to port 519, ip_address must be specified.
        :param destination_id: Int: Syslog destination papertrail ID.
        :param destination: Destination: A Destination object produced by this library.
        :param description: Optional[str]: The description of this system.
        :param auto_delete: Optional[bool]: Auto delete system if idle.
        :raises: SystemsError: When an error occurs.
        :raises: TypeError / ValueError: if invalid types or invalid values are passed.
        :return: Tuple[bool, str]: The first element is a bool indicating success (True), or failure (False), The second
            element will be the message "OK" if the first element is true, and an error message indicating what went
            wrong.
        :NOTE: One of the parameters: 'destination_port', 'destination_id', 'destination', must be defined. If more
            than one is defined, then they are preferred in this order: 'destination', 'destination_id',
            'destination_port'.
        """
        # Type / value / parameter checks:
        if not isinstance(name, str):
            __type_error__("name", "str", name)
        elif len(name) == 0:
            raise ValueError("name must not be of 0 length.")
        elif host_name is not None and not isinstance(host_name, str):
            __type_error__("host_name", "str", host_name)
        elif host_name is not None and len(host_name) == 0:
            raise ValueError("host_name must not be of 0 length.")
        elif ip_address is not None and not isinstance(ip_address, str):
            __type_error__("ip_address", "str", ip_address)
        elif ip_address is not None and len(ip_address) < 7:
            raise ValueError("ip_address must be at least 7 characters.")
        elif destination_port is not None and not isinstance(destination_port, int):
            __type_error__("destination_port", "int", destination_port)
        elif destination_id is not None and not isinstance(destination_id, int):
            __type_error__("destination_id", "int", destination_id)
        elif destination is not None and not isinstance(destination, Destination):
            __type_error__("destination", "Destination", destination)
        elif description is not None and not isinstance(description, str):
            __type_error__("description", "str", description)
        elif auto_delete is not None and not isinstance(auto_delete, bool):
            __type_error__("auto_delete", "bool", auto_delete)
        # Check the host name and ip address:
        if host_name is None and ip_address is None:
            error: str = "One of host_name or ip_address must be defined."
            raise SystemsError(error)
        # Make sure that host name is defined, when using either destination_port != 514, a destination object, or a
        #   destination_id.
        if (destination_port != 514) or destination is not None or destination_id is not None:
            if host_name is None:
                error: str = ("host_name must be defined if destination_port != 514 or using destination_id, or using "
                              "a destination object, the host_name must be defined.")
                raise SystemsError(error)
        # Check for port 514, and force ip_address:
        if destination_port is not None and destination_port == 514:
            if ip_address is None:
                error: str = "If using destination_port=514, then ip_address must be defined."
                raise SystemsError(error)

        # Check destination:
        if destination is None and destination_id is None and destination_port is None:
            error: str = "One of destination, destination_id, or destination_port must be defined."
            raise SystemsError(error)
        # Build url:
        register_url = BASE_URL + "systems.json"
        # Build JSON data dict:
        json_data = {"system": {}}
        json_data['system']['name'] = name
        if host_name is not None:
            json_data['system']['hostname'] = host_name
        if ip_address is not None:
            json_data['system']['ip_address'] = ip_address
        if destination is not None:
            json_data['system']['destination_id'] = destination.id
        elif destination_id is not None:
            json_data['system']['destination_id'] = destination_id
        else:
            json_data['system']['destination_port'] = destination_port
        if description is not None:
            json_data['system']['description'] = description
        if auto_delete is not None:
            json_data['system']['auto_delete'] = auto_delete
        # Make the request:
        raw_system: dict = requests_post(url=register_url, api_key=self._api_key, json_data=json_data)
        # Convert the raw system to a system object and store:
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        system = System(api_key=self._api_key, last_fetched=utc_now, raw_system=raw_system)
        self._SYSTEMS.append(system)
        return system

    def remove(self, index: System | int | str) -> bool:
        """
        Remove a system from papertrail.
        :param index: System | int | str: The system to remove, if System, if int, it's index to remove, if str it's
            the system name that is used to look up which system to remove.
        :return: Bool: True = Successfully removed. False = Failure.
        """
        # Type checks:
        if not isinstance(index, System) and not isinstance(index, int) and not isinstance(index, str):
            raise __type_error__("index", "System | int | str", index)
        # Determine system to remove:
        sys_to_remove: Optional[System] = None
        if isinstance(index, System):
            for system in self._SYSTEMS:
                if system.id == index.id:
                    sys_to_remove = system
                    break
            if sys_to_remove is None:
                raise IndexError("System object not found.")
        elif isinstance(index, int):
            sys_to_remove = self._SYSTEMS[index]
        elif isinstance(index, str):
            for system in self._SYSTEMS:
                if system.name == index:
                    sys_to_remove = system
            if sys_to_remove is None:
                raise IndexError("System name '%s' not found." % index)

######################################################
# List like overrides:
######################################################
    def __getitem__(self, item) -> System | list[System]:
        """
        Index systems.
        :param item: Str, int, datetime: Index.
        :return: System | list[System]
        """
        if isinstance(item, str):
            for system in self._SYSTEMS:
                if system.name == item:
                    return system
            raise IndexError("Name: %s not found.")
        elif isinstance(item, int):
            return self._SYSTEMS[item]
        elif isinstance(item, slice):
            if isinstance(item.start, int):
                return self._SYSTEMS[item.start:item.stop:item.step]
            else:
                raise TypeError("Only slices by ints are supported.")
        elif isinstance(item, datetime):
            for system in self._SYSTEMS:
                if system.last_event == item:
                    return system
            raise IndexError("datetime not found in last event.")
        raise TypeError("Can only index by str, int, and datetime objects.")

    def __iter__(self) -> Iterator:
        """
        Get an iterator of systems:
        :return: Iterator
        """
        return iter(self._SYSTEMS)

    def __len__(self) -> int:
        """
        Return the number of systems.
        :return: Int
        """
        return len(self._SYSTEMS)
###################################################
# Properties:
###################################################

    @property
    def last_fetched(self) -> Optional[datetime]:
        """
        When the systems were last fetched from papertrail.
        :return: Optional[datetime]
        """
        return self._LAST_FETCHED

    @property
    def is_loaded(self) -> bool:
        """
        Has the systems list been loaded?
        :return: Bool
        """
        return self._IS_LOADED


if __name__ == '__main__':
    # Tests:
    from apiKey import API_KEY
    from Destinations import Destinations

# Turn on / off tests:
    test_list: bool = True
    test_reload: bool = False
    test_register: bool = False
    test_update: bool = True
# Load stuff:
    print("Fetching systems...")
    systems = Systems(api_key=API_KEY)
    print("Fetching destinations...")
    destinations = Destinations(api_key=API_KEY)
# test list:
    if test_list:
        for a_system in systems:
            print(a_system.name)

# Test reload
    if test_reload:
        a_system = systems[0]
        print("Reloading system [%s]..." % a_system.name)
        a_system.reload()

# Test register
    if test_register:
        print("Adding test system.")
        a_destination = destinations[0]
        new_system = systems.register(name='test2', host_name='test2', destination=a_destination, description="TEST2")
        print("Registered: %s" % new_system.name)

# Test update:
    if test_update:
        smoke = systems['smoke']
        print("Updating: %s..." % smoke.name)
        result = smoke.update(description="test")
