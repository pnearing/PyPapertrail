#!/usr/bin/env python3
"""
    File: Systems.py
"""
from typing import Optional, Iterator
from datetime import datetime
try:
    from common import BASE_URL, __type_error__, convert_to_utc, requests_get, requests_post, requests_del
    import common
    from Exceptions import SystemsError, InvalidServerResponse, ParameterError
    from Destinations import Destination
    from System import System
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import BASE_URL, __type_error__, convert_to_utc, requests_get, requests_post, requests_del
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import SystemsError, InvalidServerResponse, ParameterError
    from PyPapertrail.Destinations import Destination
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
            Self = TypeVar("Self", bound="Systems")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(128)


class Systems(object):
    """Class to store the systems as a list."""
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
    @staticmethod
    def __to_dict__() -> dict:
        """
        Create a json / pickle friendly dict.
        :return: Dict.
        """
        return_dict: dict = {
            'last_fetched': None,
            '_systems': [],
        }
        if common.SYSTEMS_LAST_FETCHED is not None:
            return_dict['last_fetched'] = common.SYSTEMS_LAST_FETCHED.isoformat()
        for system in common.SYSTEMS:
            return_dict['_systems'].append(system.__to_dict__())
        return return_dict

    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from dict created by __to_dict__()
        :param from_dict: The dict
        :return: None
        """
        try:
            common.SYSTEMS_LAST_FETCHED = None
            if from_dict['last_fetched'] is not None:
                self._last_fetched = datetime.fromisoformat(from_dict['last_fetched'])
            common.SYSTEMS = []
            for system_dict in from_dict['_systems']:
                system = System(self._api_key, from_dict=system_dict)
                common.SYSTEMS.append(system)
        except (KeyError, ValueError) as e:
            error: str = "Invalid dict passed to __from_dict__."
            SystemsError(error, exception=e)
        return

    ###############################
    # Methods:
    ###############################
    def load(self) -> None:
        """
        Load the systems list from papertrail.
        :return: None
        """
        # Set url and headers:
        list_url = BASE_URL + 'systems.json'
        system_list: list[dict] = requests_get(url=list_url, api_key=self._api_key)
        # Set last fetched time to NOW.
        common.SYSTEMS_LAST_FETCHED = convert_to_utc(datetime.utcnow())
        # Create SYSTEMS list:
        common.SYSTEMS = []
        for raw_system in system_list:
            system = System(api_key=self._api_key, last_fetched=common.SYSTEMS_LAST_FETCHED, raw_system=raw_system)
            common.SYSTEMS.append(system)
        return

    def reload(self) -> None:
        """
        Reload the systems list.
        :return: None
        """
        return self.load()

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
        :param destination_port: Optional[int]: Syslog target port. If set to port 519, ip_address must be specified.
        :param destination_id: Optional[int]: Syslog destination papertrail ID.
        :param destination: Optional[Destination]: A Destination object produced by this library.
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
        elif host_name is not None and not isinstance(host_name, str):
            __type_error__("host_name", "str", host_name)
        elif ip_address is not None and not isinstance(ip_address, str):
            __type_error__("ip_address", "str", ip_address)
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

        # Value checks:
        if len(name) == 0:
            raise ValueError("name must not be of 0 length.")
        elif host_name is not None and len(host_name) == 0:
            raise ValueError("host_name must not be of 0 length.")
        elif ip_address is not None and len(ip_address) < 7:
            raise ValueError("ip_address must be at least 7 characters.")

        # Check the host name and ip address:
        if host_name is None and ip_address is None:
            error: str = "One of host_name or ip_address must be defined."
            raise ParameterError(error)
        # Make sure that host name is defined, when using either destination_port != 514, a destination object, or a
        #   destination_id.
        if (destination_port != 514) or destination is not None or destination_id is not None:
            if host_name is None:
                error: str = ("host_name must be defined if destination_port != 514 or using destination_id, or using "
                              "a destination object, the host_name must be defined.")
                raise ParameterError(error)
        # Check for port 514, and force ip_address:
        if destination_port is not None and destination_port == 514:
            if ip_address is None:
                error: str = "If using destination_port=514, then ip_address must be defined."
                raise ParameterError(error)

        # Check destination:
        if destination is None and destination_id is None and destination_port is None:
            error: str = "One of destination, destination_id, or destination_port must be defined."
            raise ParameterError(error)
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
        utc_now = convert_to_utc(datetime.utcnow())
        system = System(api_key=self._api_key, last_fetched=utc_now, raw_system=raw_system)
        common.SYSTEMS.append(system)
        return system

    def remove(self, index: System | int | str) -> None:
        """
        Remove a system from papertrail.
        :param index: System | int | str: The system to remove, if System, if int, it's index to remove, if str it's
            the system name that is used to look up which system to remove.
        :return: None
        """
        # Type checks:
        if not isinstance(index, System) and not isinstance(index, int) and not isinstance(index, str):
            raise __type_error__("index", "System | int | str", index)
        # Determine system to remove:
        sys_to_remove: Optional[System] = None
        if isinstance(index, System):
            if sys_to_remove not in common.SYSTEMS:
                error: str = "System not found in system list."
                raise IndexError(error)
            sys_to_remove = index
        elif isinstance(index, int) or isinstance(index, str):
            sys_to_remove = self[index]
    # Remove the system:
        # Build the url:
        del_url = BASE_URL + "systems/%i.json" % sys_to_remove.id
        # Make the delete request:
        response: dict = requests_del(url=del_url, api_key=self._api_key)
        # Verify the response:
        try:
            if response['message'] != 'System deleted':
                error: str = "Unexpected server response: %s" % response['message']
                raise InvalidServerResponse(error)
        except KeyError:
            error: str = "Unexpected server response, KeyError."
            raise InvalidServerResponse(error)
        # Remove from _SYSTEMS:
        common.SYSTEMS.remove(sys_to_remove)
        return

##################################
# Getters:
##################################
    @staticmethod
    def get_by_id(search_id: int) -> System | None:
        """
        Get a system by ID.
        :param search_id: Int: The system ID to search for.
        :return: System | None
        """
        # Type check:
        if not isinstance(search_id, int):
            __type_error__("search_id", "int", search_id)
        # Null check SYSTEMS:
        if common.SYSTEMS is None:
            error: str = "Systems not loaded."
            raise SystemsError(error)
        # Search systems:
        for system in common.SYSTEMS:
            if system.id == search_id:
                return system
        return None

    @staticmethod
    def get_by_name(search_name: str) -> System | None:
        """
        Get a system by name.
        :param search_name: Str: The name to search for
        :return: Str
        """
        # type check:
        if not isinstance(search_name, str):
            __type_error__("search_name", "str", search_name)
        # Null check SYSTEMS:
        if common.SYSTEMS is None:
            error: str = "Systems not loaded."
            raise SystemsError(error)
        # Search systems:
        for system in common.SYSTEMS:
            if system.name == search_name:
                return system
        return None

    @staticmethod
    def find_in_name(search_str: str) -> list[System] | None:
        """
        Search names for a substring and return a list of matching systems.
        :param search_str: Str: The substring to search for.
        :return: list[System] | None
        """
        # type check:
        if not isinstance(search_str, str):
            __type_error__("search_str", "str", search_str)
        # Null check SYSTEMS:
        if common.SYSTEMS is None:
            error: str = "Systems not loaded."
            raise SystemsError(error)
        # Search systems:
        return_list: list[System] = []
        for system in common.SYSTEMS:
            if system.name.find(search_str) != -1:
                return_list.append(system)
        if len(return_list) == 0:
            return None
        return return_list

######################################################
# Overrides:
######################################################
    def __getitem__(self, item: str | int | datetime) -> System | list[System]:
        """
        Index systems.
        :param item: Str | int | datetime: The index, if item is a str, index by name, if item is an int index by
            ID, if item is a datetime, index by date time of the last event (produces a list).
        :raises: SystemsError: If the systems list isn't loaded.
        :return: System | list[System]
        """
        # Null check SYSTEMS:
        if common.SYSTEMS is None:
            error: str = "Systems not loaded."
            raise SystemsError(error)
        if isinstance(item, int):
            for system in common.SYSTEMS:
                if system.id == item:
                    return system
            error: str = "ID: %i not found." % item
            raise IndexError(error)
        elif isinstance(item, str):
            for system in common.SYSTEMS:
                if system.name == item:
                    return system
            error: str = "Name: %s not found." % item
            raise IndexError(error)
        elif isinstance(item, datetime):
            search_time = convert_to_utc(item)
            results: list[System] = []
            for system in common.SYSTEMS:
                if system.last_event == search_time:
                    results.append(system)
            if len(results) == 0:
                error: str = "datetime not found in last event."
                raise IndexError(error)
            return results
        error: str = "Can only index by str, int, and datetime objects."
        raise TypeError(error)

    def __iter__(self) -> Iterator[System]:
        """
        Get an iterator of systems:
        :raises: SystemsError: If the system list isn't loaded.
        :return: Iterator
        """
        # Null check SYSTEMS:
        if common.SYSTEMS is None:
            error: str = "Systems not loaded."
            raise SystemsError(error)
        # Return Iterator:
        return iter(common.SYSTEMS)

    def __len__(self) -> int:
        """
        Return the number of systems.
        :raises: SystemsError: If the system list isn't loaded.
        :return: Int
        """
        # Null check Systems:
        if common.SYSTEMS is None:
            error: str = "Systems not loaded."
            raise SystemsError(error)
        # Return len:
        return len(common.SYSTEMS)

###################################################
# Properties:
###################################################
    @property
    def last_fetched(self) -> Optional[datetime]:
        """
        When the systems were last fetched from papertrail.
        :return: Optional[datetime]
        """
        return common.SYSTEMS_LAST_FETCHED

    @property
    def is_loaded(self) -> bool:
        """
        Has the systems list been loaded?
        :return: Bool
        """
        return common.SYSTEMS is not None

    @property
    def systems(self) -> tuple[System]:
        """
        Return a tuple of Systems.
        :return: Tuple[System]
        """
        return tuple(common.SYSTEMS)


########################################################################################################################
# Test code:
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
