#!/usr/bin/env python3
"""
    File: Destinations.py
"""
from typing import Optional, Iterator
from datetime import datetime
try:
    from common import BASE_URL, __type_error__, convert_to_utc, requests_get
    import common
    from Exceptions import DestinationError
    from Destination import Destination
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import BASE_URL, __type_error__, convert_to_utc, requests_get
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import DestinationError
    from PyPapertrail.Destination import Destination

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
            Self = TypeVar("Self", bound="Destinations")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)


class Destinations(object):
    """
    Class to store a list of log destinations. Handles loading from papertrail.
    """
##########################################
# Initialize:
##########################################
    def __init__(self,
                 api_key: str,
                 from_dict: Optional[dict] = None,
                 do_load: bool = True,
                 ):
        """
        Initialize the log destinations, optionally loading from papertrail.
        :param api_key: Str: API key.
        :param from_dict: Optional[dict]: Load from a dict created by __to_dict__(). NOTE: if from_dict is not None,
                            then the parameter do_load is ignored.
        :param do_load: Bool: True = load from papertrail on initialize.
        """
        # Type checks:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "str", from_dict)
        elif not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)
        # Store api key:
        self._api_key: str = api_key
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif do_load:
            self.load()
        return

###########################
# To / From dict:
###########################
    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict created by __to_dict__().
        :param from_dict: Dict: The dict to load from.
        :return: None
        """
        try:
            common.DESTINATIONS_LAST_FETCHED = None
            if from_dict['last_fetched'] is not None:
                common.DESTINATIONS_LAST_FETCHED = datetime.fromisoformat(from_dict['last_fetched'])
            common.DESTINATIONS = []
            for destination_dict in from_dict['_destinations']:
                destination = Destination(self._api_key, from_dict=destination_dict)
                common.DESTINATIONS.append(destination)
        except (KeyError, ValueError) as e:
            error: str = "Invalid dict passed to __from_dict__()"
            raise DestinationError(error, exception=e)
        return

    @staticmethod
    def __to_dict__() -> dict:
        """
        Create a JSON / Pickle friendly dict of this Class.
        :return: Dict.
        """
        return_dict: dict = {
            'last_fetched': None,
            '_destinations': [],
        }
        if common.DESTINATIONS_LAST_FETCHED is not None:
            return_dict['last_fetched'] = common.DESTINATIONS_LAST_FETCHED.isoformat()
        for destination in common.DESTINATIONS:
            destination_dict = destination.__to_dict__()
            return_dict['_destinations'].append(destination_dict)
        return return_dict

###########################################
# Methods:
###########################################
    def load(self) -> None:
        """
        Load destinations from papertrail.
        :return: None
        """
        # Set url and make request:
        list_url = BASE_URL + 'destinations.json'
        raw_log_destinations: list[dict] = requests_get(url=list_url, api_key=self._api_key)
        # Parse the response from papertrail.
        common.DESTINATIONS = []
        common.DESTINATIONS_LAST_FETCHED = convert_to_utc(datetime.utcnow())
        for raw_destination in raw_log_destinations:
            destination = Destination(self._api_key, raw_destination=raw_destination,
                                      last_fetched=common.DESTINATIONS_LAST_FETCHED)
            common.DESTINATIONS.append(destination)
        return

#########################
# Getters:
#########################
    @staticmethod
    def get_by_id(search_id: int) -> Optional[Destination]:
        """
        Get a destination by id.
        :param search_id: Int: the ID to search for.
        :return: Destination | None
        """
        # Type check:
        if not isinstance(search_id, int):
            __type_error__("search_id", "int", search_id)
        # Null check DESTINATIONS:
        if common.DESTINATIONS is None:
            error: str = "Destinations not loaded."
            raise DestinationError(error)
        # Search destinations:
        for destination in common.DESTINATIONS:
            if destination.id == search_id:
                return destination
        return None

    @staticmethod
    def get_by_port(search_port: int) -> Optional[Destination]:
        """
        Get a destination by port number.
        :param search_port: Int: The port number to search for.
        :return: Destination | None
        """
        # Type check:
        if not isinstance(search_port, int):
            __type_error__("search_port", "int", search_port)
        # Null check DESTINATIONS:
        if common.DESTINATIONS is None:
            error: str = "Destinations not loaded."
            raise DestinationError(error)
        # search destinations:
        for destination in common.DESTINATIONS:
            if destination.syslog_port == search_port:
                return destination
        return None

    @staticmethod
    def get_by_filter(search_filter: str) -> Optional[Destination]:
        """
        Get a destination by filter.
        :param search_filter: Str: The filter to search for.
        :return: Destination | None
        """
        # Type check:
        if not isinstance(search_filter, str):
            __type_error__("search_filter", "str", search_filter)
        # Null check DESTINATIONS:
        if common.DESTINATIONS is None:
            error: str = "Destinations not loaded."
            raise DestinationError(error)
        # Search destinations:
        for destination in common.DESTINATIONS:
            if destination.filter == search_filter:
                return destination
        return None

#########################
# Overrides:
#########################
    def __getitem__(self, item: int | str) -> Destination:
        """
        Allow indexing with square brackets.
        :param item: Int | str: If item is an int, index by ID, if item is a str, index by name.
        :raises: DestinationError: If the destination list hasn't been loaded.
        :return: Destination
        """
        # Null check DESTINATIONS:
        if common.DESTINATIONS is None:
            error: str = "Destinations not loaded."
            raise DestinationError(error)
        # Do the Index by Type:
        if isinstance(item, int):
            for destination in common.DESTINATIONS:
                if destination.id == item:
                    return destination
            raise IndexError("Index by int, ID: %i not found." % item)
        elif isinstance(item, str):
            for destination in common.DESTINATIONS:
                if destination.filter == item:
                    return destination
            raise IndexError("Index by str, filter: %s not found." % item)
        raise TypeError("Can only index by int or str.")

    def __iter__(self) -> Iterator[Destination]:
        """
        Return an Iterator of destinations.
        :raises: DestinationError: If the destination list hasn't been loaded.
        :return: Iterator.
        """
        # Null check DESTINATIONS:
        if common.DESTINATIONS is None:
            error: str = "Destinations not loaded."
            raise DestinationError(error)
        return iter(common.DESTINATIONS)

    def __len__(self) -> int:
        """
        Return number of destinations.
        :raises: DestinationError: If the destination list hasn't been loaded yet.
        :return: Int
        """
        # Null check DESTINATIONS:
        if common.DESTINATIONS is None:
            error: str = "Destinations not loaded."
            raise DestinationError(error)
        return len(common.DESTINATIONS)

###########################
# Properties:
###########################
    @property
    def last_fetched(self) -> Optional[datetime]:
        """
        The last time this list was fetched.
        :return: Optional[datetime]
        """
        return common.DESTINATIONS_LAST_FETCHED

    @property
    def is_loaded(self) -> bool:
        """
        Has the list been loaded?
        :return: Bool
        """
        return common.DESTINATIONS is not None

    @property
    def destinations(self) -> tuple[Destination]:
        """
        Return a tuple of destinations.
        :return: Tuple[Destination]
        """
        return tuple(common.DESTINATIONS)


########################################################################################################################
# Test Code:
########################################################################################################################
# Test code:
if __name__ == '__main__':
    from apiKey import API_KEY
    print("Loading destinations...")
    destinations = Destinations(API_KEY, do_load=True)
    for _destination in destinations:
        print(_destination.id, ":", _destination.syslog_port)
