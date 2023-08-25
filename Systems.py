#!/usr/bin/env python3
from __future__ import annotations
import sys
if sys.version_info.major != 3 or sys.version_info.minor < 10:
    print("Only python >= 3.10 supported")
    exit(1)
# Define Self:
try:
    from typing import Self
except ImportError:
    try:
        from typing_extensions import Self
    except (ModuleNotFoundError, ImportError):
        try:
            from typing import TypeVar
            Self = TypeVar("Self", bound="Systems")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(128)
from typing import Optional, Iterator
from datetime import datetime, timezone
from common import BASE_URL, __type_error__, requests_get, requests_post
from Exceptions import SystemsError
from Destinations import Destination
from System import System

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

    def remove(self, index: System | int | str) -> tuple[bool, str]:
        """
        Remove a system from papertrail.
        :param index: System | int | str: The system to remove, if System, if int, it's index to remove, if str it's
            the system name that is used to look up which system to remove.
        :return: Tuple[bool, str]: The first element, the bool, is True for success and False for failure.
            If True, the second element will be the message "OK", and if False, the second element will be an error
            message.
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
                return False, "System object not found."
        elif isinstance(index, int):
            try:
                sys_to_remove = self._SYSTEMS[index]
            except IndexError:
                return False, "Index %i out of bounds." % index
        elif isinstance(index, str):
            for system in self._SYSTEMS:
                if system.name == index:
                    sys_to_remove = system
            if sys_to_remove is None:
                return False, "System name '%s' not found." % index
        # Remove the system:
        # TODO: Remove the system.
        return True, "OK"

######################################################
# Overrides:
######################################################
    def __getitem__(self, item: str | int | datetime | slice) -> System | list[System]:
        """
        Index systems.
        :param item: Str, int, datetime | slice: The index, if item is a str, index by name, if item is an int index as
            a list, if item is a datetime, index by date time of the last event.
        :return: System | list[System]
        """
        if isinstance(item, int):
            return self._SYSTEMS[item]
        elif isinstance(item, str):
            for system in self._SYSTEMS:
                if system.name == item:
                    return system
            raise IndexError("Name: %s not found.")
        elif isinstance(item, datetime):
            for system in self._SYSTEMS:
                if system.last_event == item:
                    return system
            raise IndexError("datetime not found in last event.")
        elif isinstance(item, slice):
            error: str = "Systems can only be sliced by ints."
            if not isinstance(item.start, int):
                raise TypeError(error)
            elif item.stop is not None and not isinstance(item.stop, int):
                raise TypeError(error)
            elif item.step is not None and not isinstance(item.step, int):
                raise TypeError(error)
            return self._SYSTEMS[item]
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


########################################################################################################################
# TEst code:
########################################################################################################################
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

