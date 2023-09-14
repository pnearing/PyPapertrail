#!/usr/bin/env python3
"""
    File: Exceptions.py
    Papertrail Exceptions and Warnings.
"""
import requests
from requests.models import CaseInsensitiveDict
from requests import HTTPError


########################################################################################################################
# Exceptions:
########################################################################################################################
class ParameterError(Exception):
    """
    Exception to throw when a parameter error occurs.
    """
    def __init__(self, error_message: str) -> None:
        """
        Initialize the ParameterError
        :param error_message: Str: The error message.
        """
        self.error_message: str = error_message
        return

    def __str__(self) -> str:
        return self.error_message


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

    def __str__(self) -> str:
        return self.error_message


class BadRequestError(PapertrailError):
    """
    Exception to throw when there is a bad request.
    """
    def __init__(self, papertrail_message: str, **kwargs) -> None:
        """
        Initialize a bad request error.
        :param papertrail_message: Message from papertrail json.
        :param kwargs: Any additional key word arguments.
        """
        message: str = "400: Bad Request: papertrail error: %s" % papertrail_message
        PapertrailError.__init__(self, message, **kwargs)
        return


class AuthenticationError(PapertrailError):
    """
    Exception when given an invalid API key.
    """
    def __init__(self, **kwargs):
        """
        Initialize an authentication error.
        :param kwargs: Any additional key work arguments.
        """
        message: str = "401: Unauthorized: Invalid API key."
        PapertrailError.__init__(self, message, **kwargs)
        return


class NotFoundError(PapertrailError):
    """
    Exception to raise when getting a 404, Shouldn't see this in practice.
    """
    def __init__(self, url: str, **kwargs):
        """
        Initialize a 404.
        :param kwargs: Any additional key word arguments.
        """
        message = "404: Not Found: url=%s" % url
        PapertrailError.__init__(self, message, **kwargs)
        return


class MethodNotAllowedError(PapertrailError):
    """
    Exception to raise when calling an invalid method.
    """
    def __init__(self, **kwargs):
        """
        Initialize a method not found error.
        :param kwargs: Any additional arguments.
        """
        message: str = ("405: Method Not Allowed. Methods applied to an endpoint where they are not supported return "
                        "405.")
        PapertrailError(message, **kwargs)
        return


class RateLimitError(PapertrailError):
    """
    Exception to throw when a rate limit error occurs.
    """
    def __init__(self, headers: CaseInsensitiveDict, **kwargs):
        """
        Initialize a rate limit error.
        :param headers: Dict: The request headers.
        :param kwargs: Any additional key word arguments.
        """
        message = "429: Rate Limit Exceeded."
        PapertrailError.__init__(self, message, **kwargs)
        self.limit = headers['X-Rate-Limit-Limit']
        self.remaining = headers['X-Rate-Limit-Remaining']
        self.reset = headers['X-Rate-Limit-Reset']
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


class DestinationError(PapertrailError):
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


class EventError(PapertrailError):
    """
    Exception to throw if an error happens during Event processing.
    """
    def __init__(self, error_message: str, **kwargs) -> None:
        """
        Initialize an event error.
        :param error_message: Str: Message explaining the error.
        :param kwargs: Any additional key word arguments.
        """
        PapertrailError.__init__(self, error_message, **kwargs)
        return


class InvalidServerResponse(PapertrailError):
    """
    Exception to throw when the server sends invalid JSON.
    """
    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message: str = "Server sent invalid JSON."
        PapertrailError.__init__(self, message, **kwargs)
        return


class UnhandledHTTPError(PapertrailError):
    """
    Exception to raise when encountering an unhandled HTTP Error code.
    """
    def __init__(self, status_code: int, exception: HTTPError, **kwargs):
        """
        Initialize an unhandled http error.
        :param status_code: Int: The http status code.
        :param exception: Requests.HTTPError: The HTTPError from requests library.
        :param kwargs: Any additional key word arguments.
        """
        message: str = "Unhandled HTTP Status Code: %i" % status_code
        PapertrailError.__init__(self, message, **kwargs)
        self.exception = exception
        return


class RequestReadTimeout(PapertrailError):
    """
    Exception to throw when a read timeout occurs.
    """
    def __init__(self, url: str, **kwargs):
        """
        Initialize a read timeout error.
        :param url: The url being requested.
        :param kwargs: Any additional key word arguments.
        """
        message: str = "Read timeout while reading from: %s" % url
        PapertrailError.__init__(self, message, **kwargs)
        return


class UnhandledRequestsError(PapertrailError):
    """
    Exception to throw when a requests.RequestException happens.
    """
    def __init__(self, url: str, method: str, exception: requests.RequestException, **kwargs):
        """
        Initialize an unhandled requests.RequestException.
        :param url: Str: The url that was requested.
        :param method: Str: The method that was called, IE: put, post, get.
        :param exception: A requests.RequestException: The exception that happened.
        :param kwargs: Any additional key word arguments.
        """
        message: str = "requests.RequestException:method='%s', url='%s', error_num=%i, strerror=%s" % (
                                                                                                method,
                                                                                                url,
                                                                                                exception.errno,
                                                                                                exception.strerror
                                                                                            )
        PapertrailError.__init__(self, message, **kwargs)
        self.url: str = url
        self.method: str = method
        return


########################################################################################################################
# Warnings:
########################################################################################################################
class PapertrailWarning(Warning):
    """
    Warning to raise when runtime warnings occur.
    """
    pass
