#!/usr/bin/env python3
from typing import Optional
from datetime import datetime, timezone
import requests
from common import BASE_URL
from Exceptions import SystemsError


class System(object):
    """Class to store a single system."""

    def __init__(self,
                 api_key: str,
                 raw_system: Optional[dict] = None,
                 from_dict: Optional[dict] = None,
                 ) -> None:
        """
        Initialize a System object:
        :param api_key: Str: The api key.
        :param raw_system: Dict: The dict received from papertrail.
        :param from_dict: Dict: The dict created by __to_dict__().
        :raises: SystemsError: If raw_system and from_dict are either both None or both defined, or if an invalid
            raw_system dict, or from_dict dict are lacking a key.
        :returns: None
        """
        # Store the api key.
        self._api_key: str = api_key
        # Define the properties:
        self._id: int
        self._name: str
        self._last_event: Optional[datetime]
        self._auto_delete: bool
        self._json_info_link: str
        self._html_info_link: str
        self._search_link: str
        self._ip_address: Optional[str]
        self._host_name: Optional[str]
        self._syslog_host_name: str
        self._syslog_port: int
        self._last_fetched: datetime
        # Load from raw_system, or from_dict:
        if raw_system is None and from_dict is None:
            error: str = "Either raw_system must be defined, but not both."
            raise SystemsError(error)
        elif raw_system is not None and from_dict is not None:
            error: str = "Either raw_system must be defined, but not both."
            raise SystemsError(error)
        elif raw_system is not None:
            # Parse the raw_system dict:
            self.__from_raw_system__(raw_system)
        else:
            self.__from_dict__(from_dict)
        return

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
                self._last_event = datetime.fromisoformat(raw_system['last_event_at'][:-1]).replace(
                    tzinfo=timezone.utc)
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
                self._last_event = datetime.fromisoformat(from_dict['last_event']).replace(tzinfo=timezone.utc)
            self._auto_delete = from_dict['auto_delete']
            self._json_info_link = from_dict['json_link']
            self._html_info_link = from_dict['html_link']
            self._search_link = from_dict['search_link']
            self._ip_address = from_dict['ip_address']
            self._host_name = from_dict['host_name']
            self._syslog_host_name = from_dict['syslog_host']
            self._syslog_port = from_dict['syslog_port']
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
            'last_fetched': self._last_fetched,
        }
        if self._last_event is not None:
            return_dict['last_event'] = self._last_event.isoformat()
        return return_dict

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

    def reload(self, raise_on_error: bool = True) -> tuple[bool, str]:
        """
        Reload data from papertrail.
        :param raise_on_error: Bool: True, raise SystemsError when an error occurs, False, return False on error.
        :raises: SystemsError: When a request error or a JSON error occurs.
        :return: Tuple[bool, str]: The first element, the bool, is True upon success, and False upon failure.
            If the first element is True, the second element will be the message "OK", otherwise if False, the second
            element will be a message describing the error.
        """
        url = self._json_info_link
        headers = {'X-Papertrail-Token': self._api_key}
        # Request the data from papertrail:
        try:
            r = requests.get(url, headers=headers)
        except requests.ReadTimeout as e:
            error: str = "ReadTimeout: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise SystemsError(error, exception=e)
            else:
                return False, error
        # Check request status:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            error: str = "HTTPError: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise SystemsError(error, exception=e, request=r)
            else:
                return False, error
        except requests.RequestException as e:
            error: str = "RequestException: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise SystemsError(error, exception=e, request=r)
            else:
                return False, error
        # Parse JSON response:
        try:
            raw_system: dict = r.json()
        except requests.JSONDecodeError as e:
            error = "Server sent bad JSON: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise SystemsError(error, exception=e, request=r)
            else:
                return False, error
        self.__from_raw_system__(raw_system)
        return True, "OK"


class Systems(object):
    """Class to store the systems as a list."""
    _SYSTEMS: list[System] = []

    def __init__(self, api_key: str, do_load: bool = True) -> None:
        """
        Initialize the systems list.
        :param api_key: Str: The api key.
        :param do_load: Bool: True, make request from papertrail, False do not.
        :raises: SystemsError: On request error, or if invalid JSON is returned.
        """
        self._api_key: str = api_key
        self._last_fetched: Optional[datetime] = None
        self._is_loaded: bool = False
        if do_load:
            self.load()
        return

    @property
    def last_fetched(self) -> Optional[datetime]:
        """
        When the systems were last fetched from papertrail.
        :return: Optional[datetime]
        """
        return self._last_fetched

    @property
    def is_loaded(self) -> bool:
        """
        Has the systems list been loaded?
        :return: Bool
        """
        return self._is_loaded

    def load(self, raise_on_error: bool = True) -> tuple[bool, str]:
        # Set url and headers:
        url = BASE_URL + 'systems.json'
        headers = {'X-Papertrail-Token': self._api_key}
        # Make api http request:
        try:
            r = requests.get(url, headers=headers)
        except requests.ReadTimeout as e:
            error: str = "Read timeout: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise SystemsError(error, exception=e)
            else:
                return False, error
        # Check HTTP status:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            error: str = "Request HTTP error #%i:%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise SystemsError(error, exception=e, request=r)
            else:
                return False, error
        except requests.RequestException as e:
            error: str = "Request exception: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise SystemsError(error, exception=e, request=r)
            else:
                return False, error
        # Parse response:
        try:
            system_list: list[dict] = r.json()
        except requests.JSONDecodeError as e:
            error: str = "Server sent invalid JSON: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise SystemsError(error, exception=e, request=r)
            else:
                return False, error
        # Create SYSTEMS list:
        for raw_system in system_list:
            system = System(self._api_key, raw_system)
            self._SYSTEMS.append(system)
        self._is_loaded = True
        self._last_fetched = datetime.utcnow().replace(tzinfo=timezone.utc)
        return True, "OK"


if __name__ == '__main__':
    # Tests:
    from apiKey import API_KEY

    print("Fetching systems...")
    systems = Systems(API_KEY)
    a_system = systems._SYSTEMS[0]
    a_system.reload()
    exit(0)
