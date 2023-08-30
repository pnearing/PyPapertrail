#!/usr/bin/env python3
"""
    File: Papertrail.py
"""
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
import common
from common import __type_error__
from Archives import Archives
from Destinations import Destinations
from Groups import Groups
from Systems import Systems
from Exceptions import PapertrailError


class Papertrail(object):
    """
    Class for all papertrail objects.
    """

    def __init__(self,
                 api_key: str,
                 from_dict: Optional[dict] = None,
                 do_load: bool = True,
                 use_warnings: bool = True,
                 ) -> None:
        """
        Initialize papertrail interface.
        :param api_key: Str: The api key.
        :param from_dict: Dict: Load from a dict created by __to_dict__(), NOTE: if from_dict is used, do_load is
            ignored.
        :param do_load: Bool: Load from papertrail. Default = True.
        :param use_warnings: Bool: Use warnings. Default = True.
        :returns: None
        """
        # Type check:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        elif not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)
        elif not isinstance(use_warnings, bool):
            __type_error__("use_warnings", "bool", use_warnings)
        # Store use_warnings:
        common.USE_WARNINGS = use_warnings

        # Define Papertrail objects:
        self._archives: Archives = Archives(api_key=api_key, from_dict=None, do_load=False)
        self._destinations: Destinations = Destinations(api_key=api_key, from_dict=None, do_load=False)
        self._systems: Systems = Systems(api_key=api_key, from_dict=None, do_load=False)
        self._groups: Groups = Groups(api_key=api_key, from_dict=None, do_load=False)

        # Load this instance:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif do_load:
            self._archives.load()
            self._destinations.load()
            self._systems.load()
            self._groups.load()
        return

####################################
# Load / Save:
####################################
    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict created by __to_dict__().
        :param from_dict:
        :return: None
        """
        try:
            self._archives.__from_dict__(from_dict['archives'])
            self._destinations.__from_dict__(from_dict['destinations'])
            self._systems.__from_dict__(from_dict['systems'])
            self._groups.__from_dict__(from_dict['groups'])
        except KeyError:
            error: str = "Invalid dict provided to __from_dict__()."
            raise PapertrailError(error)
        return

    def __to_dict__(self) -> dict:
        """
        Return a JSON / Pickle friendly dict.
        :return: Dict
        """
        return_dict: dict = {
            'archives': self._archives.__to_dict__(),
            'destinations': self._destinations.__to_dict__(),
            'groups': self._groups.__to_dict__(),
            'systems': self._systems.__to_dict__()
        }
        return return_dict


########################################################################################################################
# TEST CODE:
########################################################################################################################
if __name__ == '__main__':
    from apiKey import API_KEY
    papertrail = Papertrail(api_key=API_KEY, do_load=True)
    exit(0)
