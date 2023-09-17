#!/usr/bin/env python3
"""
    File: Usage.py
"""
from typing import Optional
from datetime import datetime
try:
    from common import BASE_URL, __type_error__, requests_get, convert_to_utc
    import common
    from Exceptions import UsageError, InvalidServerResponse
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import BASE_URL, __type_error__, requests_get, convert_to_utc
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import UsageError, InvalidServerResponse

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
            Self = TypeVar("Self", bound="Usage")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)


class Usage(object):
    """
    Class to store usage data.
    """
    _DATA_USED: int = -1
    _DATA_PERCENT: float = -1
    _DATA_PLAN_LIMIT: int = -1
    _DATA_HARD_LIMIT: int = -1
    _IS_LOADED: bool = False
    _LAST_FETCHED: Optional[datetime] = None

    def __init__(self,
                 api_key: str,
                 from_dict: Optional[dict] = None,
                 do_load: bool = True,
                 ) -> None:
        """
        Initialize a usage object.
        :param api_key: Str: The api key.
        :param from_dict: Optional[dict]: The dict provided by __to_dict__(), NOTE: if from dict is defined, do_load
            is ignored.
        :param do_load: Bool: Load from papertrail.
        """
        # Type check:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        elif not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)

        # Store api_key:
        self._api_key: str = api_key

        # Load this instance:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif do_load:
            self.load()
        return

############################
# To / From Dict:
############################
    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict created by __to_dict__()
        :param from_dict: Dict: The dict to load from.
        :return: None
        """
        try:
            self._DATA_USED = from_dict['used']
            self._DATA_PERCENT = from_dict['used_percent']
            self._DATA_PLAN_LIMIT = from_dict['plan_limit']
            self._DATA_HARD_LIMIT = from_dict['hard_limit']
            self._LAST_FETCHED = None
            if from_dict['last_fetched'] is not None:
                self._LAST_FETCHED = datetime.fromisoformat(from_dict['last_fetched'])
        except (KeyError, ValueError):
            error: str = "Invalid dict passed to __from_dict__"
            raise UsageError(error)
        return

    def __to_dict__(self) -> dict:
        """
        Create a json / pickle friendly dict.
        :return: Dict.
        """
        return_dict: dict = {
            'used': self._DATA_USED,
            'used_percent': self._DATA_PERCENT,
            'plan_limit': self._DATA_PLAN_LIMIT,
            'hard_limit': self._DATA_HARD_LIMIT,
            'last_fetched': None,
        }
        if self._LAST_FETCHED is not None:
            return_dict['last_fetched'] = self._LAST_FETCHED.isoformat()
        return return_dict

###################################
# Methods:
###################################
    def load(self) -> None:
        """
        Load from papertrail.
        :return: None
        """
        # Build usage url.
        usage_url = BASE_URL + 'accounts.json'
        # Make the request:
        response: dict = requests_get(usage_url, self._api_key)
        # Parse the response:
        try:
            self._DATA_USED = response['log_data_transfer_used']
            self._DATA_PERCENT = response['log_data_transfer_used_percent']
            self._DATA_PLAN_LIMIT = response['log_data_transfer_plan_limit']
            self._DATA_HARD_LIMIT = response['log_data_transfer_hard_limit']
        except KeyError as e:
            error: str = "KeyError while parsing data from papertrail. Key: '%s' not found." % str(e)
            raise InvalidServerResponse(error)
        self._IS_LOADED = True
        self._LAST_FETCHED = convert_to_utc(datetime.utcnow())
        return

    def reload(self) -> None:
        """
        Reload from Papertrail.
        :return: None
        """
        return self.load()

#############################
# Properties:
#############################
    @property
    def data_used(self) -> int:
        """
        Data used in bytes.
        :return: Int
        """
        return self._DATA_USED

    @property
    def data_used_percent(self) -> float:
        """
        Data used percentage.
        :return: Float
        """
        return self._DATA_PERCENT

    @property
    def plan_limit(self) -> int:
        """
        Data plan limit in bytes.
        :return: Int
        """
        return self._DATA_PLAN_LIMIT

    @property
    def hard_limit(self) -> int:
        """
        Hard limit in bytes.
        :return: Int
        """
        return self._DATA_HARD_LIMIT

    @property
    def is_loaded(self) -> bool:
        """
        If the usage has been loaded.
        :return: Bool
        """
        return self._IS_LOADED

    @property
    def last_fetched(self) -> Optional[datetime]:
        """
        Last datetime this was last loaded from Papertrail in UTC.
        :return: Optional[datetime]: None if not loaded.
        """
        return self._LAST_FETCHED


########################################################################################################################
# TEST CODE:
########################################################################################################################
if __name__ == '__main__':
    from apiKey import API_KEY
    u = Usage(API_KEY, do_load=True)
    print("Data used:", u.data_used)
    print("Percent used: %0.2f" % u.data_used_percent)
    print("Plan limit:", u.plan_limit)
    print("Hard limit:", u.hard_limit)
    exit(0)
