#!/usr/bin/env python3
"""
Common variables / functions for papertrail api.
"""
from typing import Any, NoReturn
from datetime import datetime
from requests import Response, JSONDecodeError, HTTPError
from Exceptions import BadRequestError, AuthenticationError, NotFoundError, MethodNotAllowedError, RateLimitError
from Exceptions import InvalidServerResponse, UnhandledHTTPError

BASE_URL: str = 'https://papertrailapp.com/api/v1/'


def is_timezone_aware(dt: datetime) -> bool:
    """
    Checks if a given datetime object is timezone-aware.
    :param dt: The datetime object to check.
    :return: Bool, True if timezone-aware, False if timezone-unaware.
    """
    #
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def __type_error__(argument_name: str, desired_types: str, received_obj: Any) -> NoReturn:
    """
    Raise a TypeError with a good message.
    :param argument_name: Str: String of the variable name.
    :param desired_types: Str: String of desired type(s).
    :param received_obj: The var which was received, note: type() will be called on it.
    :return: NoReturn
    """
    error: str = "TypeError: argument:%s, got %s type, expected: %s" % (argument_name,
                                                                        str(type(received_obj)), desired_types)
    raise TypeError(error)


def __raise_for_http_error__(request: Response, exception: HTTPError) -> NoReturn:
    """
    Raise the appropriate Exception on known http errors.
    :param request: A requests.Response object: The request with the http error.
    :param exception: An Exception object: The exception (requests.HTTPError) that caused something to be raised.
    :return: None | NoReturn: NoReturn if a known error, None if an unknown error.
    """
    if request.status_code == 400:  # Bad Request
        try:
            error_dict = request.json()
        except JSONDecodeError as e:
            raise InvalidServerResponse(exception=e, request=request, orig_exception=exception)
        try:
            raise BadRequestError(error_dict['message'], request=request, exception=exception)
        except KeyError as e:
            raise InvalidServerResponse(exception=e, request=request, orig_exception=exception)
    elif request.status_code == 401:    # Unauthorized
        raise AuthenticationError(request=request, exception=exception)
    elif request.status_code == 404:    # Not Found
        raise NotFoundError(request.url, request=request, exception=exception)
    elif request.status_code == 405:    # MethodNotAllowed
        raise MethodNotAllowedError(request=request, exception=exception)
    elif request.status_code == 429:  # Rate Limit Exceeded
        raise RateLimitError(headers=request.headers, request=request, exception=exception)
    else:
        raise UnhandledHTTPError(request.status_code, exception=exception, request=request)