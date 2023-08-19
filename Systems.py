#!/usr/bin/env python3
from datetime import datetime, timezone
import requests
from common import BASE_URL

class SystemError(Exception):
    """Class to raise on error while looking at systems"""

class System(object):
    """Class to store a single system."""
    def __init__(self, api_key: str) -> None:
        return


class Systems(object):
    """Class to store the systems as a list."""
    _SYSTEMS: list[System] = []

    def __init__(self, api_key: str, do_load: bool = True) -> None:
        self._api_key: str = api_key
        if do_load:
            self.load()
        return

    def load(self, raise_on_error: bool = True):
        # Set url and headers:
        url = BASE_URL + 'systems.json'
        headers = {'X-Papertrail-Token': self._api_key}
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
        except requests.HTTPError as e:
            error: str = "Request HTTP error #%i:%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise ArchiveError(error)
            else:
                return False, error

        return
