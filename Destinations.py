#!/usr/bin/env python3
from typing import Optional, Iterator
from datetime import datetime, timezone
import requests
from common import BASE_URL, __type_error__
from Exceptions import DestinationError


class Destination(object):
    """
    Class storing a single log destination.
    """

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
        return

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
        self._description = raw_destination['description']
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


class Destinations(object):
    """
    Class to store a list of log destinations. Handles loading from papertrail.
    """
    _DESTINATIONS: list[Destination] = []
    _IS_LOADED: bool = False
    _LAST_FETCHED: Optional[datetime] = None

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
        # Store api key:
        self._api_key: str = api_key
        if from_dict is not None:
            if not isinstance(from_dict, dict):
                __type_error__("dict", from_dict)
            self.__from_dict__(from_dict)
        elif do_load:
            self.load()
        return

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

    def load(self, raise_on_error: bool = True) -> tuple[bool, str]:
        # Set url and headers:
        list_url = BASE_URL + 'destinations.json'
        headers = {'X-Papertrail-Token': self._api_key}
        # Make request:
        try:
            r = requests.get(list_url, headers=headers)
        except requests.ReadTimeout as e:
            error: str = "ReadTimeout: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise DestinationError(error, exception=e)
            else:
                return False, error
        # Check request status:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            error: str = "HTTPError: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise DestinationError(error, exception=e, request=r)
            else:
                return False, error
        # Parse request JSON:
        try:
            raw_log_destinations = r.json()
        except requests.JSONDecodeError as e:
            error: str = "Server sent invalid JSON: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise DestinationError(error, exception=e, request=r)
            else:
                return False, error
        # Parse the response from papertrail.
        self._DESTINATIONS = []
        for raw_destination in raw_log_destinations:
            destination = Destination(self._api_key, raw_destination)
            self._DESTINATIONS.append(destination)
        self._IS_LOADED = True
        self._LAST_FETCHED = datetime.utcnow().replace(tzinfo=timezone.utc)
        return True, "OK"

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


# Test code:
if __name__ == '__main__':
    from apiKey import API_KEY
    print("Loading destinations...")
    destinations = Destinations(API_KEY, do_load=True)
