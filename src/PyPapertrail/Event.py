#!/usr/bin/env python3
"""
    File: Event.py
"""
from typing import Optional
from datetime import datetime
from warnings import warn
try:
    from common import __type_error__
    import common
    from Exceptions import EventError, ParameterError, InvalidServerResponse, PapertrailWarning
    from System import System
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import __type_error__
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import EventError, ParameterError, InvalidServerResponse, PapertrailWarning
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
            Self = TypeVar("Self", bound="Groups")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)


class Event(object):
    """
    Class to store an event.
    """
#####################
# Initialize:
#####################
    def __init__(self,
                 raw_event: Optional[dict] = None,
                 from_dict: Optional[dict] = None,
                 ) -> None:
        """
        Initialize an Event object:
        :param raw_event: Optional[dict]: The dict provided by Papertrail.
        :param from_dict: Optional[dict]: A dict provided by __to_dict__().
        """
        # Type checks:
        if raw_event is not None and not isinstance(raw_event, dict):
            __type_error__("raw_event", "Optional[dict]", raw_event)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        # Parameter checks:
        if (raw_event is None and from_dict is None) or (raw_event is not None and from_dict is not None):
            error: str = "raw_event, or from_dict must be defined, but not both."
            raise ParameterError(error)
        # Initialize the properties:
        self._id: int = -1
        self._source_ip: str = ''
        self._program: Optional[str] = None
        self._message: str = ''
        self._received_at: datetime
        self._generated_at: datetime
        self._display_received_at: str = ''
        self._source_id: int = -1
        self._source_name: str = ''
        self._host_name: str = ''
        self._system: Optional[System] = None
        self._severity: str = ''
        self._facility: str = ''
        # Warn if systems not loaded.
        if not common.SYSTEMS and not common.SYSTEM_WARNING_MADE and common.USE_WARNINGS:
            warning: str = "Systems not loaded, not linking to systems."
            warn(warning, PapertrailWarning)
            common.SYSTEM_WARNING_MADE = True

        # Load the instance:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif raw_event is not None:
            self.__from_raw_event__(raw_event)
        return

    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load this instance from a dict provided by __to_dict__().
        :param from_dict: Dict: The dict provided by __to_dict__().
        :return: None
        """
        try:
            self._id = from_dict['id']
            self._source_ip = from_dict['ip']
            self._program = from_dict['program']
            self._message = from_dict['message']
            self._received_at = datetime.fromisoformat(from_dict['received'])
            self._generated_at = datetime.fromisoformat(from_dict['generated'])
            self._display_received_at = from_dict['display_time']
            self._source_id = from_dict['source_id']
            self._source_name = from_dict['source_name']
            self._host_name = from_dict['host_name']
            self._severity = from_dict['severity']
            self._facility = from_dict['facility']
            if common.SYSTEMS:
                for system in common.SYSTEMS:
                    if system.id == self._source_id:
                        self._system = system
                        break
        except (KeyError, ValueError) as e:
            error: str = "Invalid dict provided to from_dict."
            raise EventError(error, exception=e)

    def __to_dict__(self) -> dict:
        """
        Create a json / Pickle friendly dict.
        :return: Dict
        """
        return_dict = {
            'id': self._id,
            'ip': self._source_ip,
            'program': self._program,
            'message': self._message,
            'received': self._received_at.isoformat(),
            'generated': self._generated_at.isoformat(),
            'display_time': self._display_received_at,
            'source_id': self._source_id,
            'source_name': self._source_name,
            'host_name': self._host_name,
            'severity': self._severity,
            'facility': self._facility
        }
        return return_dict

    def __from_raw_event__(self, raw_event: dict) -> None:
        """
        Load from an event dict provided by Papertrail.
        :param raw_event: Dict: The dict provided by papertrail.
        :return: None
        """
        try:
            self._id = int(raw_event['id'])
            self._source_ip = raw_event['source_ip']
            self._program = raw_event['program']
            self._message = raw_event['message']
            self._received_at = datetime.fromisoformat(raw_event['received_at'])
            self._generated_at = datetime.fromisoformat(raw_event['generated_at'])
            self._display_received_at = raw_event['display_received_at']
            self._source_id = raw_event['source_id']
            self._source_name = raw_event['source_name']
            self._host_name = raw_event['hostname']
            self._severity = raw_event['severity']
            self._facility = raw_event['facility']
            if common.SYSTEMS:
                for system in common.SYSTEMS:
                    if system.id == self._source_id:
                        self._system = system
                        break
        except (KeyError, ValueError) as e:
            error: str = "KeyError while processing event."
            raise InvalidServerResponse(error, exeption=e)
        return

####################################
# Properties:
####################################
    @property
    def id(self) -> int:
        """
        Event ID.
        :return: Int
        """
        return self._id

    @property
    def source_ip(self) -> str:
        """
        Source IP address.
        :return: Str.
        """
        return self._source_ip

    @property
    def program(self) -> Optional[str]:
        """
        Program, can be None if not defined by papertrail.
        :return: Str
        """
        return self._program

    @property
    def message(self) -> str:
        """
        Message
        :return: Str.
        """
        return self._message

    @property
    def received_at(self) -> datetime:
        """
        Datetime object for when this was received.
        :return: Datetime object.
        """
        return self._received_at

    @property
    def generated_at(self) -> datetime:
        """
        Datetime object for when this was generated.
        :return: Datetime object.
        """
        return self._generated_at

    @property
    def display_received_at(self) -> str:
        """
        Display received at time.
        :return: Str.
        """
        return self._display_received_at

    @property
    def source_id(self) -> int:
        """
        The source system ID of this event
        :return: Int.
        """
        return self._source_id

    @property
    def source_name(self) -> str:
        """
        The name of the source system.
        :return: Str.
        """
        return self._source_name

    @property
    def host_name(self) -> str:
        """
        The source host name generating this event.
        :return: Str.
        """
        return self._host_name

    @property
    def severity(self) -> str:
        """
        The severity of the event.
        :return: Str.
        """
        return self._severity

    @property
    def facility(self) -> str:
        """
        The logging facility.
        :return: Str.
        """
        return self._facility


# ########################################################################################################################
# # TEST CODE:
# ########################################################################################################################
# if __name__ == '__main__':
#     from apiKey import API_KEY
#
#     exit(0)
