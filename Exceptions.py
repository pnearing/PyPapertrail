#!/usr/bin/env python3

class PapertrailError(Exception):
    """
    Base Exception for Papertrail objects.
    """
    def __init__(self, error_message: str, **kwargs) -> None:
        """
        Base Exception for Papertrail Errors.
        :param error_message: Message explaining the error.
        :param kwargs: Any additional key word arguments.
        """
        self.error_message: str = error_message
        self.key_word_args: dict = kwargs
        return


class SystemsError(PapertrailError):
    """
    Exception to raise when system api calls produce an error.
    """
    def __init__(self, error_message: str, **kwargs) -> None:
        """
        Initialize a system error.
        :param error_message: Message explaining the error.
        :param kwargs: Any additional key word arguments.
        """
        PapertrailError.__init__(self, error_message, **kwargs)
        return


class GroupError(PapertrailError):
    """
    Exception to raise when groups api calls produce an error.
    """
    def __init__(self, error_message: str, **kwargs) -> None:
        """
        Initialize a group error.
        :param error_message: Message explaining the error.
        :param kwargs: Any additional key word arguments.
        """
        PapertrailError.__init__(self, error_message, **kwargs)
        return


class SavedSearchError(PapertrailError):
    """
    Exception to raise when a saved search opi call produces an error.
    """
    def __init__(self, error_message: str, **kwargs) -> None:
        """
        Initialize a saved search error.
        :param error_message: Message explaining the error.
        :param kwargs: Any additional key word arguments.
        """
        PapertrailError.__init__(self, error_message, **kwargs)
        return


class LogDestinationError(PapertrailError):
    """
    Exception to raise when a log destination api call produces an error.
    """
    def __init__(self, error_message: str, **kwargs) -> None:
        """
        Initialize a log destination error.
        :param error_message: Message explaining the error.
        :param kwargs: Any additional keyword arguments.
        """
        PapertrailError.__init__(self, error_message, **kwargs)
        return


class UsersError(PapertrailError):
    """
    Exception to raise when a user's opi call produces an error.
    """
    def __init__(self, error_message: str, **kwargs) -> None:
        """
        Initialize a user's error.
        :param error_message: Message explaining the error.
        :param kwargs: Any additional key word arguments.
        """
        PapertrailError.__init__(self, error_message, **kwargs)
        return


class UsageError(PapertrailError):
    """
    Exception to raise when an account usage produces an error.
    """
    def __init__(self, error_message: str, **kwargs) -> None:
        """
        Initialize an account usage error.
        :param error_message: Message explaining the error.
        :param kwargs: Any additional key word arguments.
        """
        PapertrailError.__init__(self, error_message, **kwargs)
        return


class ArchiveError(PapertrailError):
    """
    Exception to raise when archive api calls produce an error.
    """
    def __init__(self, error_message: str, **kwargs) -> None:
        """
        Initialize an archive error
        :param error_message: Message explaining the error.
        :param kwargs: Any additional key word arguments.
        """
        PapertrailError.__init__(self, error_message, **kwargs)
        return


class QueryError(PapertrailError):
    """
    Exception to raise when a search query api call produces an error.
    """
    def __init__(self, error_message: str, **kwargs) -> None:
        """
        Initialize a search query error.
        :param error_message: Message explaining the error.
        :param kwargs: Any additional key word arguments.
        """
        PapertrailError.__init__(self, error_message, **kwargs)
        return
