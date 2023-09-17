#!/usr/bin/env python3
"""
    File: SavedSearch.py
"""
from typing import Optional
from datetime import datetime
try:
    from common import __type_error__, requests_get, requests_put, convert_to_utc
    import common
    from Exceptions import SavedSearchError, InvalidServerResponse, ParameterError
    from Group import Group
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import __type_error__, requests_get, requests_put, convert_to_utc
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import SavedSearchError, InvalidServerResponse, ParameterError
    from PyPapertrail.Group import Group

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
            Self = TypeVar("Self", bound="SavedSearch")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)


class SavedSearch(object):
    """
    Class to store a single saved search.
    """
######################
# Initialize:
#####################
    def __init__(self,
                 api_key: str,
                 from_dict: Optional[dict] = None,
                 raw_search: Optional[dict] = None,
                 last_fetched: Optional[datetime] = None,
                 ) -> None:
        """
        Initialize a saved search.
        :param api_key: Str: The api key.
        :param from_dict: Optional[dict]: A dict provided by __to_dict__().
        :param raw_search: Optional[dict]: A dict provided by Papertrail, NOTE: if using raw_search, last_fetched must
            be defined.
        :param last_fetched: Optional[datetime]: A datetime object for when this was last fetched.
        """
        # Type Check:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        elif raw_search is not None and not isinstance(raw_search, dict):
            __type_error__("raw_search", "Optional[dict]", raw_search)
        elif last_fetched is not None and not isinstance(last_fetched, datetime):
            __type_error__("last_fetched", "Optional[datetime]", last_fetched)
        # Parameter checks:
        if (from_dict is None and raw_search is None) or (from_dict is not None and raw_search is not None):
            error: str = "ParameterError: Either from_dict or raw_search must be defined, but not both."
            raise ParameterError(error)
        elif raw_search is not None and last_fetched is None:
            error: str = "ParameterError: If raw_search is defined, last_fetched must also be defined."
            raise ParameterError(error)

        # Store api key:
        self._api_key: str = api_key

        # Init properties:
        self._name: str = ''
        self._id: int = -1
        self._query: str = ''
        self._group: Optional[Group] = None
        self._self_link: str = ''
        self._search_link: str = ''
        self._html_link: str = ''
        self._last_fetched: Optional[datetime] = convert_to_utc(last_fetched)

        # Load this instance:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif raw_search is not None:
            self.__from_raw_search__(raw_search)
        return

##############################
# To / From dict, and from raw_search:
##############################
    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict provided by __to_dict__()
        :param from_dict: Dict: The dict to load from.
        :return: None
        """
        # Null Check GROUPS:
        if common.GROUPS is None:
            error: str = "Groups not loaded."
            raise SavedSearchError(error)
        try:
            self._name = from_dict['name']
            self._id = from_dict['id']
            self._query = from_dict['query']
            self._group = None
            for group in common.GROUPS:
                if group.id == from_dict['group_id']:
                    self._group = group
                    break
            if self._group is None:
                error: str = "Group ID: %i not found." % from_dict['group_id']
                raise IndexError(error)
            self._self_link = from_dict['self_link']
            self._search_link = from_dict['search_link']
            self._html_link = from_dict['html_link']
            self._last_fetched = None
            if from_dict['last_fetched'] is not None:
                self._last_fetched = datetime.fromisoformat(from_dict['last_fetched'])
        except (KeyError, ValueError) as e:
            error: str = "Invalid dict passed to __from_dict__()"
            raise SavedSearchError(error, exception=e)
        return

    def __to_dict__(self) -> dict:
        """
        Return a json / pickle friendly dict.
        :return: Dict
        """
        return_dict = {
            'name': self._name,
            'id': self._id,
            'query': self._query,
            'group_id': None,
            'self_link': self._self_link,
            'search_link': self._search_link,
            'html_link': self._html_link,
            'last_fetched': None
        }
        if self._group is not None:
            return_dict['group_id'] = self._group.id
        if self._last_fetched is not None:
            return_dict['last_fetched'] = self._last_fetched.isoformat()
        return return_dict

    def __from_raw_search__(self, raw_search: dict) -> None:
        """
        Load from a dict provided by Papertrail.
        :param raw_search: Dict: The dict to load from.
        :return: None
        """
        if common.GROUPS is None:
            error: str = "Groups not loaded."
            raise SavedSearchError(error)
        try:
            self._name = raw_search['name']
            self._id = raw_search['id']
            self._query = raw_search['query']
            self._group = None
            for group in common.GROUPS:
                if group.id == raw_search['group']['id']:
                    self._group = group
                    break
            if self._group is None:
                error: str = "Group ID: '%i' not found." % raw_search['group']['id']
                raise IndexError(error)
            self._self_link = raw_search['_links']['self']
            self._search_link = raw_search['_links']['search']
            self._html_link = raw_search['_links']['html']
        except KeyError as e:
            error: str = "KeyError while accessing raw_search"
            raise InvalidServerResponse(error, exception=e)
        return

##########################
# Methods:
##########################
    def reload(self) -> None:
        """
        Reload the data for this search.
        :return: None
        """
        # Build reload url:
        reload_url = self._self_link
        # Make request to reload url:
        raw_search: dict = requests_get(url=reload_url, api_key=self._api_key)
        # Parse raw search:
        self.__from_raw_search__(raw_search)
        self._last_fetched = convert_to_utc(datetime.utcnow())
        return

    def update(self,
               name: Optional[str],
               query: Optional[str],
               group: Optional[Group | int],
               ) -> Self:
        """
        Update this saved search. Returns the updated saved search instance.
        :param name: Optional[str]: The name to set.
        :param query: Optional[str]: The query to set.
        :param group: Optional[Group | int]: The group to associate with. It can be a Group object, or an int for the
            ID of the group.
        :return: SavedSearch
        """
        # type check:
        if name is not None and not isinstance(name, str):
            __type_error__("name", "Optional[str]", name)
        elif query is not None and not isinstance(query, str):
            __type_error__("query", "Optional[str]", query)
        elif group is not None and not isinstance(group, (Group, str, int)):
            __type_error__("group", "Optional[Group | str | int]", group)
        # Check that at least one parameter is defined.
        all_none = True
        for parameter in (name, query, group):
            if parameter is not None:
                all_none = False
        if all_none:
            error: str = "ParameterError: At least one of name, query, or group must be defined."
            raise ParameterError(error)
        # Get the group ID:
        group_id: Optional[int] = None
        if group is not None:
            if isinstance(group, Group):
                if group not in common.GROUPS:
                    error: str = "Group not found."
                    raise IndexError(error)
            else:  # group is an int:
                for group in common.GROUPS:
                    if group.id == group:
                        group_id = group.id
                if group_id is None:
                    error: str = "Group ID: '%i' not found." % group
                    raise IndexError(error)
        # Get update URL:
        update_url = self._self_link
        # Build the JSON data:
        json_data: dict = {'search': {}}
        if name is not None:
            json_data['search']['name'] = name
        if query is not None:
            json_data['search']['query'] = query
        if group is not None:
            json_data['search']['group_id'] = group_id
        # Make the request:
        raw_search: dict = requests_put(url=update_url, api_key=self._api_key, json_data=json_data)
        # Parse the response:
        self.__from_raw_search__(raw_search)
        self._last_fetched = convert_to_utc(datetime.utcnow())
        return self

##########################
# Overrides:
##########################
    def __eq__(self, other: Self | int) -> bool:
        """
        Equality test. Other can be another Group, a str with the group name or an int with the group id.
        :param other: Group | str | int: If other is a group, their ids are compared, if other is a str, the name of
            the group is compared, and finally if other is an int, then the id is compared.
        :return: Bool
        """
        if isinstance(other, type(self)):
            return self._id == other._id
        elif isinstance(other, int):
            return self._id == other
        error: str = "Can't compare SavedSearch to type: %s" % str(type(other))
        raise TypeError(error)

    def __str__(self) -> str:
        """
        Refer as a string and get the name.
        :return: Str
        """
        return self._name

    def __int__(self) -> int:
        """
        Refer as an integer and get the ID.
        :return: Int
        """
        return self._id

##########################
# Properties:
##########################
    @property
    def name(self) -> str:
        """
        Name of the saved search
        :return: Str
        """
        return self._name

    @property
    def id(self) -> int:
        """
        The papertrail ID of this saved search.
        :return: Int
        """
        return self._id

    @property
    def query(self) -> str:
        """
        The query.
        :return: Str
        """
        return self._query

    @property
    def group(self) -> Group:
        """
        The group this is associated with.
        :return: Group
        """
        return self._group

    @property
    def self_link(self) -> str:
        """
        Link to this JSON object.
        :return: Str
        """
        return self._self_link

    @property
    def search_link(self) -> str:
        """
        The search link.
        :return: Str
        """
        return self._search_link

    @property
    def html_link(self) -> str:
        """
        The html info link
        :return: Str
        """
        return self._html_link

    @property
    def last_fetched(self) -> datetime:
        """
        The last time this was fetched from the server in UTC.
        :return:
        """
        return self._last_fetched


# ########################################################################################################################
# # TEST CODE:
# ########################################################################################################################
# if __name__ == '__main__':
#     from apiKey import API_KEY
#
#     exit(0)
