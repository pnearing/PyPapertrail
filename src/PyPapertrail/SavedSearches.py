#!/usr/bin/env python3
"""
    File: SavedSearches.py
"""
from typing import Optional, Iterator
from datetime import datetime
from warnings import warn
try:
    from common import USE_WARNINGS, BASE_URL, __type_error__, convert_to_utc, requests_get, requests_post
    import common
    from SavedSearch import SavedSearch
    from Exceptions import SavedSearchError, PapertrailWarning
    from Group import Group
    from Groups import Groups
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import USE_WARNINGS, BASE_URL, __type_error__, convert_to_utc, requests_get, requests_post
    import PyPapertrail.common as common
    from PyPapertrail.SavedSearch import SavedSearch
    from PyPapertrail.Exceptions import SavedSearchError, PapertrailWarning
    from PyPapertrail.Group import Group
    from PyPapertrail.Groups import Groups

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
            Self = TypeVar("Self", bound="SavedSearches")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)

# Store a 'groups' instance:
_GROUPS: Optional[Groups] = None


class SavedSearches(object):
    """
    Class to store a list of saved searches.
    """
#######################
# Initialize:
#######################
    def __init__(self,
                 api_key: str,
                 from_dict: Optional[dict] = None,
                 do_load: bool = True
                 ) -> None:
        """
        Initialize the searches instance:
        :param from_dict: Optional[dict]: The dict provided by __to_dict__(), NOTE: if from_dict is defined, then
            do_load is ignored.
        :param do_load: Bool: Load data from Papertrail on init, default = True.
        """
        # Pull in Groups:
        global _GROUPS
        # Type check:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        elif not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)
        # Store api key:
        self._api_key: str = api_key
        # Store a 'groups' instance:
        if _GROUPS is None:
            _GROUPS = Groups(api_key=api_key, from_dict=None, do_load=False)
            
        # Load this instance:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif do_load:
            self.load()
        return

##############################
# To / from dict:
##############################
    def __from_dict__(self, from_dict: dict) -> None:
        try:
            common.SEARCHES_LAST_FETCHED = None
            if from_dict['last_fetched'] is not None:
                common.SEARCHES_LAST_FETCHED = datetime.fromisoformat(from_dict['last_fetched'])
            common.SEARCHES = []
            for search_dict in from_dict['_searches']:
                search = SavedSearch(api_key=self._api_key, from_dict=search_dict)
                common.SEARCHES.append(search)
        except (KeyError, ValueError) as e:
            error: str = "Invalid dict passed to __from_dict__()"
            raise SavedSearchError(error, exception=e)
        return

    @ staticmethod
    def __to_dict__() -> dict:
        """
        Return a JSON / pickle friendly dict.
        :return: Dict
        """
        return_dict: dict = {
            'last_fetched': None,
            '_searches': [],
        }
        if common.SEARCHES_LAST_FETCHED is not None:
            return_dict['last_fetched'] = common.SEARCHES_LAST_FETCHED.isoformat()
        for search in common.SEARCHES:
            return_dict['_searches'].append(search.__to_dict__())
        return return_dict
    
###############################
# Methods:
###############################
    def load(self) -> None:
        """
        Load data from Papertrail.
        :return: None
        """
        # Build list url:
        list_url: str = BASE_URL + 'searches.json'
        # Make the request:
        response: list[dict] = requests_get(url=list_url, api_key=self._api_key)
        # Parse the response:
        common.SEARCHES_LAST_FETCHED = convert_to_utc(datetime.utcnow())
        common.SEARCHES = []
        for raw_search in response:
            search = SavedSearch(api_key=self._api_key,
                                 raw_search=raw_search,
                                 last_fetched=common.SEARCHES_LAST_FETCHED
                                 )
            common.SEARCHES.append(search)
        return

    def reload(self) -> None:
        """
        Reload data from Papertrail.
        :return: None
        """
        return self.load()

    def create(self,
               name: str,
               query: str,
               group: Optional[Group | str | int] = None,
               ) -> SavedSearch:
        """
        Create a new saved search.
        :param name: Str: The name of the search.
        :param query: Str: Query to run.
        :param group: Optional[Group | str | int]: The group to associate with, if not specified, it will attach to all
            systems, or the first group. Either a group object, a str for the group name, and an int for the group id.
        :return: SavedSearch: The newly created saved search object.
        """
        # Type check:
        if not isinstance(name, str):
            __type_error__("name", "str", name)
        elif not isinstance(query, str):
            __type_error__("query", "str", query)
        elif group is not None:
            if not isinstance(group, Group) and not isinstance(group, str) and not isinstance(group, int):
                __type_error__("group", "Optional[Group | str | int]", group)
        # Value check name and query:
        if len(name) == 0:
            error: str = "name cannot be an empty string."
            raise ValueError(error)
        elif len(query) == 0:
            error: str = "query cannot be an empty string."
            raise ValueError(error)
        # Build the creation url:
        create_url = BASE_URL + 'searches.json'
        # Build the JSON Data:
        json_data: dict = {'search': {
            'name': name,
            'query': query,
        }}
        if group is not None:
            # Load groups if required:
            if not _GROUPS.is_loaded:
                if USE_WARNINGS:
                    warning: str = "Loading group information from Papertrail."
                    warn(warning, PapertrailWarning)
                _GROUPS.load()
            # Set group_id:
            group_id: int
            if isinstance(group, Group):
                if group not in _GROUPS:
                    error: str = "Group not found in groups."
                    raise IndexError(error)
                group_id = group.id
            else:
                group_obj = _GROUPS[group]  # Raises IndexError if not found.
                group_id = group_obj.id
            # Add group id to json:
            json_data['search']['group_id'] = group_id
        # Make the request:
        raw_search: dict = requests_post(url=create_url, api_key=self._api_key, json_data=json_data)
        # Parse the response:
        last_fetched = convert_to_utc(datetime.utcnow())
        new_search = SavedSearch(api_key=self._api_key, raw_search=raw_search, last_fetched=last_fetched)
        common.SEARCHES.append(new_search)
        return new_search

###############################
# Getters:
###############################
    @staticmethod
    def get_by_name(name: str) -> Optional[list[SavedSearch]]:
        """
        Return a list of saved searches matching a given name. Returns None if not found.
        :param name: Str: The name to search for.
        :raises SavedSearchError: If the saved search list isn't loaded.
        :return: Optional[list[SavedSearch]]
        """
        # Type check:
        if not isinstance(name, str):
            __type_error__("name", "str", name)
        # Null check SEARCHES:
        if common.SEARCHES is None:
            error: str = "Saved searches not loaded."
            raise SavedSearchError(error)
        # Do the search:
        results: list[SavedSearch] = []
        for search in common.SEARCHES:
            if search.name == name:
                results.append(search)
        if len(results) == 0:
            return None
        return results

    @staticmethod
    def get_by_query(query: str) -> Optional[list[SavedSearch]]:
        """
        Get a list of saved searches by query, returns None if not found.
        :param query: Str: The query to search for.
        :raises SavedSearchError: If the saved search list isn't loaded.
        :return: Optional[list[SavedSearch]]
        """
        # type check:
        if not isinstance(query, str):
            __type_error__("query", "str", query)
        # Null check SEARCHES:
        if common.SEARCHES is None:
            error: str = "Saved searches not loaded."
            raise SavedSearchError(error)
        # Do the search:
        results: list[SavedSearch] = []
        for search in common.SEARCHES:
            if search.query == query:
                results.append(search)
        if len(results) == 0:
            return None
        return results

    @staticmethod
    def find_in_name(search_name: str) -> Optional[list[SavedSearch]]:
        """
        Find in names, run name.find() and if a result, returns it, None if not found.
        :param search_name: Str: The search string to find in names.
        :return: Optional[list[SavedSearch]]
        """
        # Type check:
        if not isinstance(search_name, str):
            __type_error__("search_name", "str", search_name)
        # Null check SEARCHES:
        if common.SEARCHES is None:
            error: str = "Searches not loaded."
            raise SavedSearchError(error)
        # Do search:
        results: list[SavedSearch] = []
        for search in common.SEARCHES:
            if search.name.find(search_name) > -1:
                results.append(search)
        if len(results) == 0:
            return None
        return results

    @staticmethod
    def find_in_query(search_query: str) -> Optional[list[SavedSearch]]:
        """
        Find in query string, runs query.find() and if a result returns it, None if not found.
        :param search_query: Str: The search string to find in the query.
        :return: Optional[list[SavedSearch]]
        """
        # type check:
        if not isinstance(search_query, str):
            __type_error__("search_query", "str", search_query)
        # Null check SEARCHES:
        if common.SEARCHES is None:
            error: str = "Searches not loaded."
            raise SavedSearchError(error)
        # Do Search:
        results: list[SavedSearch] = []
        for search in common.SEARCHES:
            if search.query.find(search_query) > -1:
                results.append(search)
        if len(results) == 0:
            return None
        return results

###############################
# Overrides:
###############################
    def __getitem__(self, item: str | int) -> SavedSearch | list[SavedSearch]:
        """
        Allow square bracketing by str or int.
        :param item: Str | int: If item is a str, return a list of searches by name, otherwise if item is an int return
            the saved search that matches that ID.
        :raises IndexError: If name is not found.
        :raises TypeError: If anything other than a str is passed.
        :raises SavedSearchError: If the search list hasn't been loaded.
        :return: SavedSearch | list[SavedSearch]
        """
        if common.SEARCHES is None:
            error: str = "Saved searches not loaded."
            raise SavedSearchError(error)
        if isinstance(item, str):
            results = []
            for search in common.SEARCHES:
                if search.name == item:
                    results.append(search)
            if len(results) == 0:
                error: str = "IndexError: Name: '%s' not found." % item
                raise IndexError(error)
            return results
        elif isinstance(item, int):
            for search in common.SEARCHES:
                if search.id == item:
                    return search
            error: str = "IndexError: ID: '%i' not found." % item
            raise IndexError(error)
        error: str = "TypeError: Can only index by str or int."
        raise TypeError(error)

    def __len__(self) -> int:
        """
        Number of saved searches
        :raise SavedSearchError: If the saved search list isn't loaded.
        :return: Int
        """
        # Null check SEARCHES:
        if common.SEARCHES is None:
            error: str = "Saved searches not loaded."
            raise SavedSearchError(error)
        # Return the len:
        return len(common.SEARCHES)

    def __iter__(self) -> Iterator[SavedSearch]:
        """
        Return an iterator over the searches.
        :raises SavedSearchError: If the saved search list isn't loaded.
        :return: Iterator
        """
        # Null check SEARCHES:
        if common.SEARCHES is None:
            error: str = "Saved searches not loaded."
            raise SavedSearchError(error)
        # Return The iterator:
        return iter(common.SEARCHES)

###############################
# Properties:
###############################
    @property
    def searches(self) -> tuple[SavedSearch]:
        """
        Return a tuple of searches.
        :return: Tuple[SavedSearch]
        """
        return tuple(common.SEARCHES)

    @property
    def last_fetched(self) -> datetime:
        """
        Last time this was loaded from the server.
        :return: Datetime object.
        """
        return common.SEARCHES_LAST_FETCHED

    @property
    def is_loaded(self) -> bool:
        """
        Has this been loaded in some way.
        :return: Bool.
        """
        return common.SEARCHES is not None


########################################################################################################################
# TEST CODE:
########################################################################################################################
if __name__ == '__main__':
    from apiKey import API_KEY
    saved_searches = SavedSearches(api_key=API_KEY)
    for saved_search in saved_searches:
        print(saved_search.name, ":", saved_search.query)

    test_create: bool = False
    test_update: bool = True
    test_delete: bool = False

    if test_create:
        test_groups = Groups(api_key=API_KEY)
        test_name = "TEST"
        test_query = "*"
        test_group = test_groups.groups[0]
        saved_searches.create(name=test_name, query=test_query, group=test_group)

    if test_update:
        saved_search = saved_searches['TEST']

    exit(0)
