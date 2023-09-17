#!/usr/bin/env python3
"""
    File: Results.py
"""
from typing import Optional
from datetime import datetime
try:
    from common import __type_error__
    import common
    from Event import Event
    from Exceptions import QueryError, InvalidServerResponse, ParameterError
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import __type_error__
    import PyPapertrail.common as common
    from PyPapertrail.Event import Event
    from PyPapertrail.Exceptions import QueryError, InvalidServerResponse, ParameterError
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
            Self = TypeVar("Self", bound="SearchResults")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)


class Results(object):
    """
    Class to store search results.
    """
##########################
# Initialize:
##########################
    def __init__(self,
                 raw_results: Optional[dict] = None,
                 from_dict: Optional[dict] = None,
                 ) -> None:
        """
        Initialize the search results:
        :param raw_results: Optional[dict]: The results dict provided by Papertrail.
        :param from_dict: Optional[dict]: A dict provided by __to_dict__().
        :raises ParameterError: If an invalid parameter combination is provided.
        :raises TypeError: If an invalid type is passed.
        :raises InvalidServerResponse: If a key isn't found in the papertrail dict.
        :raises QueryError: If an invalid dict is passed to from_dict.
        """
        # Type checks:
        if raw_results is not None and not isinstance(raw_results, dict):
            __type_error__("raw_results", "Optional[dict]", raw_results)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        # Parameter checks:
        if (raw_results is None and from_dict is None) or (raw_results is not None and from_dict is not None):
            error: str = "Either raw_results or from_dict must be defined, but not both."
            raise ParameterError(error)
        # Initialize properties:
        self._min_id: int = -1
        self._max_id: int = -1
        self._reached_beginning: Optional[bool] = None
        self._min_time_at: Optional[datetime] = None
        self._max_time_at: Optional[datetime] = None
        self._reached_time_limit: Optional[bool] = None
        self._reached_record_limit: Optional[bool] = None
        self._reached_end: Optional[bool] = None
        self._sawmill:  Optional[bool] = None
        self._events: tuple[Event]

        # Load this instance:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif raw_results is not None:
            self.__from_raw_results__(raw_results)
        return

    def __from_raw_results__(self, raw_results: dict) -> None:
        """
        Load this instance from raw results provided by papertrail.
        :param raw_results: Dict: The dict provided by papertrail.
        :return: None
        """
        try:
            self._min_id = raw_results['min_id']
            self._max_id = raw_results['max_id']
            if 'reached_beginning' in raw_results.keys():
                self._reached_beginning = raw_results['reached_beginning']
            if 'min_time_at' in raw_results.keys():
                self._min_time_at = datetime.fromisoformat(raw_results['min_time_at'])
            if 'max_time_at' in raw_results.keys():
                self._max_time_at = datetime.fromisoformat(raw_results['max_time_at'])
            if 'reached_time_limit' in raw_results.keys():
                self._reached_time_limit = raw_results['reached_time_limit']
            if 'reached_record_limit' in raw_results.keys():
                self._reached_record_limit = raw_results['reached_record_limit']
            if 'reached_end' in raw_results.keys():
                self._reached_end = raw_results['reached_end']
            if 'sawmill' in raw_results.keys():
                self._sawmill = raw_results['sawmill']
            events = []
            for raw_event in raw_results['events']:
                event = Event(raw_event=raw_event)
                events.append(event)
            self._events = tuple(events)
        except (KeyError, ValueError) as e:
            error: str = "KeyError or ValueError while decoding Papertrail response dict."
            raise InvalidServerResponse(error, exception=e)
        return

    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load this instance from a dict provided by __to_dict__().
        :param from_dict: Dict: The dict provided by __to_dict__().
        :return: None
        """
        try:
            self._min_id = from_dict['min_id']
            self._max_id = from_dict['max_id']
            self._reached_beginning = from_dict['beginning']
            self._min_time_at = None
            if from_dict['min_time'] is not None:
                self._min_time_at = datetime.fromisoformat(from_dict['min_time'])
            self._max_time_at = None
            if from_dict['max_time'] is not None:
                self._max_time_at = datetime.fromisoformat(from_dict['max_time'])
            self._reached_time_limit = from_dict['time_limit']
            self._reached_record_limit = from_dict['record_limit']
            self._reached_end = from_dict['end']
            self._sawmill = from_dict['sawmill']
            events = []
            for event_dict in from_dict['event']:
                event = Event(from_dict=event_dict)
                events.append(event)
            self._events = tuple(events)
        except (KeyError, ValueError) as e:
            error: str = "Bad dict passed to __from_dict__."
            raise QueryError(error, exception=e)
        return

    def __to_dict__(self) -> dict:
        """
        Return a JSON / Pickle friendly dict for this instance.
        :return: Dict.
        """
        return_dict: dict = {
            'min_id': self._min_id,
            'max_id': self._max_id,
            'beginning': self._reached_beginning,
            'min_time': None,
            'max_time': None,
            'time_limit': self._reached_time_limit,
            'record_limit': self._reached_record_limit,
            'end': self._reached_end,
            'sawmill': self._sawmill,
            'events': []
        }
        if self._min_time_at is not None:
            return_dict['min_time'] = self._min_time_at.isoformat()
        if self._max_time_at is not None:
            return_dict['max_time'] = self._max_time_at.isoformat()
        for event in self._events:
            event_dict = event.__to_dict__()
            return_dict['events'].append(event_dict)
        return return_dict

################################
# Properties:
################################
    @property
    def min_id(self) -> int:
        """
        Minimum ID.
        :return: Int
        """
        return self._min_id

    @property
    def max_id(self) -> int:
        """
        Maximum ID.
        :return: Int
        """
        return self._max_id

    @property
    def reached_beginning(self) -> Optional[bool]:
        """
        Search reached beginning.
        :return: Optional[bool]
        """
        return self._reached_beginning

    @property
    def min_time_it(self) -> Optional[datetime]:
        """
        Min date time.
        :return: Optional[datetime]
        """
        return self._min_time_at

    @property
    def max_time_at(self) -> Optional[datetime]:
        """
        Max date time.
        :return: Optional[datetime]
        """
        return self._max_time_at

    @property
    def reached_time_limit(self) -> Optional[bool]:
        """
        Search reached time limit.
        :return: Optional[bool]
        """
        return self._reached_time_limit

    @property
    def reached_record_limit(self) -> Optional[bool]:
        """
        Search reached the record limit.
        :return: Optional[bool]
        """
        return self._reached_record_limit

    @property
    def reached_end(self) -> Optional[bool]:
        """
        The search reached the end.
        :return: Optional[bool]
        """
        return self._reached_end

    @property
    def sawmill(self) -> Optional[bool]:
        """
        Sawmill??
        :return: Optional[bool]
        """
        return self._sawmill

    @property
    def events(self) -> tuple[Event]:
        """
        The list of events.
        :return: Tuple[Event]
        """
        return self._events


# ########################################################################################################################
# # TEST CODE:
# ########################################################################################################################
# if __name__ == '__main__':
#     from apiKey import API_KEY
#
#     exit(0)
