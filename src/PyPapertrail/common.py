#!/usr/bin/env python3
"""
Common variables / functions for papertrail api.
"""
import sys
from typing import Any, NoReturn, Optional, TypeVar
from datetime import datetime
import pytz
import requests
try:
    from Exceptions import BadRequestError, AuthenticationError, NotFoundError, MethodNotAllowedError, RateLimitError
    from Exceptions import InvalidServerResponse, UnhandledHTTPError, RequestReadTimeout, UnhandledRequestsError
    import RateLimits
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.Exceptions import BadRequestError, AuthenticationError, NotFoundError, MethodNotAllowedError, RateLimitError
    from PyPapertrail.Exceptions import InvalidServerResponse, UnhandledHTTPError, RequestReadTimeout, UnhandledRequestsError
    import PyPapertrail.RateLimits as RateLimits

Archive = TypeVar("Archive", bound="Archive")
Destination = TypeVar("Destination", bound="Destination")
Group = TypeVar("Group", bound="Group")
SavedSearch = TypeVar("SavedSearch", bound="SavedSearch")
System = TypeVar("System", bound="System")
User = TypeVar("User", bound="User")

ARCHIVES: Optional[list[Archive]] = None
DESTINATIONS: Optional[list[Destination]] = None
GROUPS: Optional[list[Group]] = None
SEARCHES: Optional[list[SavedSearch]] = None
SYSTEMS: Optional[list[System]] = None
USERS: Optional[list[User]] = None

ARCHIVES_LAST_FETCHED: Optional[datetime] = None
DESTINATIONS_LAST_FETCHED: Optional[datetime] = None
GROUPS_LAST_FETCHED: Optional[datetime] = None
SEARCHES_LAST_FETCHED: Optional[datetime] = None
SYSTEMS_LAST_FETCHED: Optional[datetime] = None
USERS_LAST_FETCHED: Optional[datetime] = None

BASE_URL: str = 'https://papertrailapp.com/api/v1/'
USE_WARNINGS: bool = True
SYSTEM_WARNING_MADE: bool = False


def __version_check__() -> Optional[NoReturn]:
    """
    Check the python version and exit gracefully if we're running the wrong version.
    :return: Optional[NoReturn]
    """
    if sys.version_info.major != 3 or sys.version_info.minor < 10:
        print("Only python >= 3.10 supported")
        exit(1)
    return


def is_timezone_aware(dt: datetime) -> bool:
    """
    Checks if a given datetime object is timezone-aware.
    :param dt: The datetime object to check.
    :return: Bool, True if timezone-aware, False if timezone-unaware.
    """
    #
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def convert_to_utc(date_time_obj: datetime) -> datetime:
    """
    Takes a datetime object that is either timezone-aware or timezone-naive, and returns a datetime object that is
    timezone-aware and is in UTC time.
    :param date_time_obj: Datetime object: The datetime to convert.
    :return: Datetime: Timezone-aware UTC datetime.
    """
    if is_timezone_aware(date_time_obj):
        return date_time_obj.astimezone(pytz.utc)
    return pytz.utc.localize(date_time_obj)


def parse_limit_header(headers: requests.models.CaseInsensitiveDict[str]) -> None:
    """
    Parse the rate limit headers.
    :param headers: Dict: The headers.
    :raises IndexError | ValueError: If an invalid dict is passed.
    :return: None
    """
    # Type check:
    if not isinstance(headers, requests.models.CaseInsensitiveDict):
        __type_error__("headers", "requests.models.CaseInsensitiveDict", headers)
    RateLimits.limit = int(headers['X-Rate-Limit-Limit'])
    RateLimits.remaining = int(headers['X-Rate-Limit-Remaining'])
    RateLimits.reset = int(headers['X-Rate-Limit-Reset'])
    return


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


def __raise_for_http_error__(request: requests.Response, exception: requests.HTTPError) -> NoReturn:
    """
    Raise the appropriate Exception on known http errors.
    :param request: A requests.Response object: The request with the http error.
    :param exception: An Exception object: The exception (requests.HTTPError) that caused something to be raised.
    :return: None | NoReturn: NoReturn if a known error, None if an unknown error.
    """
    if request.status_code == 400:  # Bad Request
        try:
            error_dict = request.json()
        except requests.JSONDecodeError as e:
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
    raise UnhandledHTTPError(request.status_code, exception=exception, request=request)


def requests_get(url: str,
                 api_key: str,
                 returns_json: bool = True
                 ) -> Optional[list | dict]:
    """
    Make a requests.get() call, and return the json data.
    :param url: Str: The url to get.
    :param api_key: Str: The api key
    :param returns_json: Bool: The request returns JSON, default = True.
    :return: List | dict: The response data.
    """
    # Generate headers:
    headers = {'X-Papertrail-Token': api_key}
    # Make the request.
    try:
        request = requests.get(url, headers=headers)
    except requests.ReadTimeout as e:
        raise RequestReadTimeout(url, exception=e)
    except requests.RequestException as e:
        raise UnhandledRequestsError(url=url, method="GET", exception=e)
    # Parse the HTTP Status:
    try:
        request.raise_for_status()
    except requests.HTTPError as e:
        __raise_for_http_error__(request=request, exception=e)
    # Parse rate limit headers:
    parse_limit_header(request.headers)
    # If we're not expecting JSON, return None:
    if not returns_json:
        return None
    # Parse the JSON data:
    try:
        response: list | dict = request.json()
    except requests.JSONDecodeError as e:
        raise InvalidServerResponse(request=request, exception=e)
    return response


def requests_post(url: str,
                  api_key: str,
                  json_data: Any,
                  returns_json: bool = True,
                  ) -> Optional[list | dict]:
    """
    Make a requests.post() call, and return the json data.
    :param url: Str: The url to post to.
    :param api_key: Str: The API Key.
    :param json_data: Any: The json data to post.
    :param returns_json: Bool: The request returns JSON.
    :return: A list | dict: The server response.
    """
    # Generate headers:
    headers = {
        'X-Papertrail-Token': api_key,
        'Content-Type': 'application/json',
    }
    # Make the request:
    try:
        request = requests.post(url, headers=headers, json=json_data)
    except requests.ReadTimeout as e:
        raise RequestReadTimeout(url=url, exception=e)
    except requests.RequestException as e:
        raise UnhandledRequestsError(url=url, method="POST", exception=e)
    # Parse the HTTP Status:
    try:
        request.raise_for_status()
    except requests.HTTPError as e:
        __raise_for_http_error__(request=request, exception=e)
    # Parse rate limit headers:
    parse_limit_header(request.headers)
    # If the request doesn't return JSON data, return None.
    if not returns_json:
        return None
    # Parse the JSON data:
    try:
        response: list | dict = request.json()
    except requests.JSONDecodeError as e:
        raise InvalidServerResponse(request=request, exception=e)
    return response


def requests_put(url: str,
                 api_key: str,
                 json_data: Any,
                 returns_json: bool = True
                 ) -> Optional[list | dict]:
    """
    Make a requests.put() call, and return the json response data.
    :param url: Str: The url to put to.
    :param api_key: Str: The API Key
    :param json_data: Any: The json data to send.
    :param returns_json: Bool: The request returns JSON data, default=True.
    :return: A list | dict: The server response data.
    """
    # Generate headers:
    headers = {
        "X-Papertrail-Token": api_key,
        "Content-Type": "application/json",
    }
    # Make the request:
    try:
        request = requests.put(url, headers=headers, json=json_data)
    except requests.ReadTimeout as e:
        raise RequestReadTimeout(url=url, exception=e)
    # Parse HTTP Status:
    try:
        request.raise_for_status()
    except requests.HTTPError as e:
        __raise_for_http_error__(request=request, exception=e)
    except requests.RequestException as e:
        raise UnhandledRequestsError(url=url, method="PUT", exception=e)
    # Parse rate limit headers:
    parse_limit_header(request.headers)
    # If we're not expecting JSON, return None:
    if not returns_json:
        return None
    # Parse the JSON data:
    try:
        response: list | dict = request.json()
    except requests.JSONDecodeError as e:
        raise InvalidServerResponse(request=request, exception=e)
    return response


def requests_del(url: str,
                 api_key: str,
                 returns_json: bool = True
                 ) -> Optional[dict]:
    """
    Send a 'delete' request to the given url.
    :param url: Str: The url to send the request to.
    :param api_key: Str: The API Key.
    :param returns_json: Bool: The request returns JSON data, default = True.
    :return: Dict: JSON Decoded response.
    """
    # Generate headers:
    headers = {'X-Papertrail-Token': api_key}
    # Make the request:
    try:
        request = requests.delete(url, headers=headers)
    except requests.ReadTimeout as e:
        raise RequestReadTimeout(url=url, exception=e)
    except requests.RequestException as e:
        raise UnhandledRequestsError(url=url, method="DELETE", exception=e)
    # Parse rate limit headers:
    parse_limit_header(request.headers)
    # If we're not expecting JSON, return None
    if not returns_json:
        return None
    # Parse the JSON data:
    try:
        response: dict = request.json()
    except requests.JSONDecodeError as e:
        raise InvalidServerResponse(request=request, exception=e)
    return response
