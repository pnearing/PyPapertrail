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
            Self = TypeVar("Self", bound="Destinations")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)
from typing import Optional, Iterator
from datetime import datetime, timezone
from common import BASE_URL, __type_error__, requests_get
from Exceptions import DestinationError
from Destination import Destination


class Destinations(object):
    """
    Class to store a list of log destinations. Handles loading from papertrail.
    """
    _DESTINATIONS: list[Destination] = []
    _IS_LOADED: bool = False
    _LAST_FETCHED: Optional[datetime] = None

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
            if not isinstance(from_dict, dict):
                __type_error__("from_dict", "dict", from_dict)
            self.__from_dict__(from_dict)
        elif do_load:
            self.load()
        return

###########################
# Load / Save functions:
###########################
    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict created by __to_dict__().
        :param from_dict: Dict: The dict to load from.
        :return: None
        """
        self._LAST_FETCHED = None
        if from_dict['last_fetched'] is not None:
            self._LAST_FETCHED = datetime.fromisoformat(from_dict['last_fetched']).replace(tzinfo=timezone.utc)
        self._DESTINATIONS = []
        for destination_dict in from_dict['_destinations']:
            destination = Destination(self._api_key, from_dict=destination_dict)
            self._DESTINATIONS.append(destination)
        return

    def __to_dict__(self) -> dict:
        """
        Create a JSON / Pickle friendly dict of this Class.
        :return: Dict.
        """
        return_dict: dict = {
            'last_fetched': None,
            '_destinations': [],
        }
        if self._LAST_FETCHED is not None:
            return_dict['last_fetched'] = self._LAST_FETCHED.isoformat()
        for destination in self._DESTINATIONS:
            destination_dict = destination.__to_dict__()
            return_dict['_destinations'].append(destination_dict)
        return return_dict

#########################
# Overrides:
#########################
    def __getitem__(self, item) -> Destination | list[Destination]:
        """
        Index _DESTINATIONS as a list.
        :param item: Int | slice: Index to return.
        :return: Destination.
        """
        if isinstance(item, int) or isinstance(item, slice):
            return self._DESTINATIONS[item]
        raise TypeError("Can only index by int.")

    def __iter__(self) -> Iterator:
        """
        Return an Iterator.
        :return: Iterator.
        """
        return iter(self._DESTINATIONS)

    def __len__(self) -> int:
        """
        Return number of destinations.
        :return: Int
        """
        return len(self._DESTINATIONS)

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
        self._DESTINATIONS = []
        self._LAST_FETCHED = datetime.utcnow().replace(tzinfo=timezone.utc)
        for raw_destination in raw_log_destinations:
            destination = Destination(self._api_key, raw_destination=raw_destination, last_fetched=self._LAST_FETCHED)
            self._DESTINATIONS.append(destination)
        self._IS_LOADED = True
        return

    ###########################
# Properties:
###########################
    @property
    def last_fetched(self) -> Optional[datetime]:
        """
        The last time this list was fetched.
        :return: Optional[datetime]
        """
        return self._LAST_FETCHED

    @property
    def is_loaded(self) -> bool:
        """
        Has the list been loaded?
        :return: Bool
        """
        return self._IS_LOADED


########################################################################################################################
# Test Code:
########################################################################################################################
# Test code:
if __name__ == '__main__':
    from apiKey import API_KEY
    print("Loading destinations...")
    destinations = Destinations(API_KEY, do_load=True)
