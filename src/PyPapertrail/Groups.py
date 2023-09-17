#!/usr/bin/env python3
"""
    File: Groups.py
"""
from typing import Optional, Iterator
from datetime import datetime
import pytz
try:
    from common import BASE_URL, __type_error__, convert_to_utc, requests_get, requests_post, requests_del
    import common
    from Exceptions import GroupError, InvalidServerResponse
    from Group import Group
    from System import System
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import BASE_URL, __type_error__, convert_to_utc, requests_get, requests_post, requests_del
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import GroupError, InvalidServerResponse
    from PyPapertrail.Group import Group
    from PyPapertrail.System import System

# Version Check:
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


class Groups(object):
    """Class to represent all the groups."""
    ###################################
    # Initialize:
    ###################################
    def __init__(self, api_key: str, from_dict: Optional[dict] = None, do_load: bool = True):
        """
        Initialize all the groups, loading from papertrail if requested.
        :param api_key: Str: The api key.
        :param from_dict: Optional[dict]: The dict created by __to_dict__(); Note: that if from_dict is not None, then
            the do_load option is ignored. Default = None
        :param do_load: Bool: Load from Papertrail, True = Load, False = Don't load. Default = True.
        """
        # Type checks:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        elif not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)
        # Store api_key:
        self._api_key = api_key

        # Load the groups:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif do_load:
            self.load()
        return

    ########################################
    # To / From dict methods:
    ########################################
    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load from a dict created by __to_dict__()
        :param from_dict: Dict: The dict provided by __to_dict__().
        :return: Dict.
        """
        try:
            common.GROUPS_LAST_FETCHED = None
            if from_dict['last_fetched'] is not None:
                common.GROUPS_LAST_FETCHED = datetime.fromisoformat(from_dict['last_fetched'])
            common.GROUPS = []
            for group_dict in from_dict['_groups']:
                group = Group(api_key=self._api_key, from_dict=group_dict)
                common.GROUPS.append(group)
        except (KeyError, ValueError) as e:
            error: str = "Invalid dict passed to __from_dict__()"
            raise GroupError(error, exception=e)
        return

    @staticmethod
    def __to_dict__() -> dict:
        """
        Store this list of groups as a json / pickle friendly dict.
        :return: Dict
        """
        return_dict: dict = {
            'last_fetched': None,
            '_groups': [],
        }
        if common.GROUPS_LAST_FETCHED is not None:
            return_dict['last_fetched'] = common.GROUPS_LAST_FETCHED.isoformat()
        for group in common.GROUPS:
            group_dict = group.__to_dict__()
            return_dict['_groups'].append(group_dict)
        return return_dict

    #########################
    # Methods:
    #########################
    def load(self) -> Self:
        """
        Load from papertrail.
        :return: Groups: The loaded groups.
        """
        # Build url and make request:
        list_url = BASE_URL + "groups.json"
        raw_groups: list[dict] = requests_get(url=list_url, api_key=self._api_key)
        # Parse the response from papertrail:
        common.GROUPS = []
        common.GROUPS_LAST_FETCHED = pytz.utc.localize(datetime.utcnow())
        for raw_group in raw_groups:
            group = Group(api_key=self._api_key, raw_group=raw_group, last_fetched=common.GROUPS_LAST_FETCHED)
            common.GROUPS.append(group)
        return self

    def reload(self) -> Self:
        """
        Reload the data.
        :return: Groups: The updated groups.
        """
        return self.load()

    def create(self,
               name: str,
               system_wildcard: Optional[str] = None,
               systems: Optional[list[System | str | int]] = None,
               ) -> Group:
        """
        Create a new group.
        :param name: Str: The Name of the new group.
        :param system_wildcard: Optional[str]: The system wildcard.
        :param systems: Optional[list[System | str | int]]: A list of systems to add to the group, Either a System
            object, an int for the system ID, or a str for the system name.
        :return: Group: The newly created Group object.
        """
        # Type Checks:
        if not isinstance(name, str):
            __type_error__("name", "str", name)
        elif system_wildcard is not None and not isinstance(system_wildcard, str):
            __type_error__("system_wildcard", "str", system_wildcard)
        elif systems is not None and not isinstance(systems, list):
            __type_error__("systems", "list[System | str | int]", systems)

        # Type Check system_ids elements:
        if systems is not None:
            for i, sys_obj in enumerate(systems):
                if not isinstance(sys_obj, (System, str, int)):
                    __type_error__("systems[%i]" % i, "System | str | int", systems[i])

        # Value check systems for an empty list:
        if systems is not None and len(systems) == 0:
            error: str = "systems cannot be an empty list."
            raise ValueError(error)

        # Null check SYSTEMS:
        if common.SYSTEMS is None:
            error = "Systems not loaded."
            raise GroupError(error)

        # Build a list of system id's
        sys_ids: list[int] = []
        if systems is not None:
            for unknown_system in systems:
                if isinstance(unknown_system, System):
                    if unknown_system not in common.SYSTEMS:
                        error: str = "System not found."
                        raise IndexError(error)
                    sys_ids.append(unknown_system.id)
                elif isinstance(unknown_system, int):
                    system_found: bool = False
                    for system in common.SYSTEMS:
                        if system.id == unknown_system:
                            sys_ids.append(system.id)
                            system_found = True
                            break
                    if not system_found:
                        error: str = "System ID: '%i' not found." % unknown_system
                        raise IndexError(error)
                else:  # unknown_system is a str:
                    system_found: bool = False
                    for system in common.SYSTEMS:
                        if system.name == unknown_system:
                            sys_ids.append(system.id)
                            system_found = True
                            break
                    if not system_found:
                        error: str = "System Name: '%s' not found." % unknown_system
                        raise IndexError(error)

        # Build url:
        create_url: str = BASE_URL + "groups.json"
        # Build JSON data object:
        json_data = {'group': {'name': name}}
        if system_wildcard is not None:
            json_data['group']['system_wildcard'] = system_wildcard
        if systems is not None:
            json_data['group']['system_ids'] = sys_ids
        # Make the request:
        raw_group: dict = requests_post(create_url, self._api_key, json_data)
        # Parse the response from papertrail:
        last_fetched = convert_to_utc(datetime.utcnow())
        group = Group(api_key=self._api_key, raw_group=raw_group, last_fetched=last_fetched)
        common.GROUPS.append(group)
        return group

    def delete(self, group_idx: Group | int | str) -> None:
        """
        Delete a group.
        :param group_idx: Group | int | str: The group to delete, either a Group object, an int, at which groups
            will be indexed by id, and a str at which point the group will be deleted by name
        :return: None
        """
        # Type checks:
        if not isinstance(group_idx, Group) and not isinstance(group_idx, int) and not isinstance(group_idx, str):
            __type_error__("group_to_delete", "Group | int | str", group_idx)
        # Get the group object:
        group_to_delete: Optional[Group] = None
        if isinstance(group_idx, Group):
            group_to_delete = group_idx
        elif isinstance(group_idx, str):
            for group in common.GROUPS:
                if group.name == group_idx:
                    group_to_delete = group
            if group_to_delete is None:
                error: str = "IndexError: group name: %s not found." % group_idx
                raise GroupError(error)
        elif isinstance(group_idx, int):
            for group in common.GROUPS:
                if group.id == group_idx:
                    group_to_delete = group
            if group_to_delete is None:
                error: str = "IndexError: group ID: %i not found." % group_idx
                raise GroupError(error)
        # Get URL and Make the 'delete' request.:
        delete_url = group_to_delete.self_link
        response: dict = requests_del(delete_url, self._api_key)
        # Parse response:
        try:
            if response['message'] != 'Group deleted':
                error: str = "Unexpected response: %s" % response['message']
                raise InvalidServerResponse(error)
        except KeyError:
            error: str = "Unexpected server response, KeyError."
            raise InvalidServerResponse(error)
        # Remove the group from the group list:
        common.GROUPS.remove(group_to_delete)
        return

###############################
# Getters:
###############################
    @staticmethod
    def get_by_id(search_id: int) -> Optional[Group]:
        """
        Get a Group by ID.
        :param search_id: Int: The id number of the group.
        :return: Group | None
        """
        # Type check:
        if not isinstance(search_id, int):
            __type_error__("search_id", "int", search_id)
        # Null check GROUPS:
        if common.GROUPS is None:
            error: str = "Groups not loaded."
            raise GroupError(error)
        # Search groups:
        for group in common.GROUPS:
            if group.id == search_id:
                return group
        return None

    @staticmethod
    def get_by_name(search_name: str) -> Optional[list[Group]]:
        """
        Get a list of Groups by name, returns None if not found.
        :param search_name: Str: The name of the group.
        :return: Group | None
        """
        # Type check:
        if not isinstance(search_name, str):
            __type_error__("search_name", "str", search_name)
        # Null check GROUPS:
        if common.GROUPS is None:
            error: str = "Groups not loaded."
            raise GroupError(error)
        # Search groups:
        results: list[Group] = []
        for group in common.GROUPS:
            if group.name == search_name:
                results.append(group)
        if len(results) == 0:
            return None
        return results

    @staticmethod
    def get_by_system(search_sys: System) -> Optional[list[Group]]:
        """
        Get a list of groups that include this system.
        :param search_sys: System: The system to search for.
        :return: Group | None
        """
        # Type check:
        if not isinstance(search_sys, System):
            __type_error__("search_sys", "System", search_sys)
        # Null check GROUPS:
        if common.GROUPS is None:
            error: str = "Groups not loaded."
            raise GroupError(error)
        # Search groups:
        return_list: list[Group] = []
        for group in common.GROUPS:
            for system in group.systems:
                if system == search_sys:
                    return_list.append(group)
                    break
        if len(return_list) == 0:
            return None
        return return_list

    @staticmethod
    def find_in_name(search_str: str) -> Optional[list[Group]]:
        """
        Search names for a substring, and return a list of groups that match.
        :param search_str: Str: The substring to search for.
        :return: list[Group] | None
        """
        # Type check:
        if not isinstance(search_str, str):
            __type_error__("search_str", "str", search_str)
        # Null check GROUPS:
        if common.GROUPS is None:
            error: str = "Groups not loaded."
            raise GroupError(error)
        # Search groups
        return_list: list[Group] = []
        for group in common.GROUPS:
            if group.name.find(search_str) != -1:
                return_list.append(group)
        if len(return_list) == 0:
            return None
        return return_list

    #############################
    # Overrides:
    #############################
    def __getitem__(self, item: int | str) -> Group | list[Group]:
        """
        Allow indexing with square brackets.
        :param item: Int | str: The index, if item is an int, index by ID, if item is a str, index by name,
        :return: Group
        """
        # Null check GROUPS:
        if common.GROUPS is None:
            error: str = "Groups not loaded."
            raise GroupError(error)
        # Do search:
        if isinstance(item, int):
            for group in common.GROUPS:
                # print("DEBUG", group.id, "==", item)
                if group.id == item:
                    return group
            error: str = "Indexing as int, id %i not found." % item
            raise IndexError(error)
        elif isinstance(item, str):
            results: list[Group] = []
            for group in common.GROUPS:
                if group.name == item:
                    results.append(group)
            if len(results) == 0:
                error: str = "Indexing as string, name '%s' not found." % item
                raise IndexError(error)
            return results
        error: str = "Can only index by Group, int, str, or slice with type int, not: %s" % str(type(item))
        raise TypeError(error)

    def __len__(self) -> int:
        """
        Return the number of groups.
        :raises: GroupError: If the group list hasn't been loaded.
        :return: Int
        """
        # Null check GROUPS:
        if common.GROUPS is None:
            error: str = "Groups not loaded."
            raise GroupError(error)
        # Return len:
        return len(common.GROUPS)

    def __iter__(self) -> Iterator[Group]:
        """
        Return an iterator of the groups.
        :raises: GroupError: If the group list hasn't been loaded.
        :return: Iterator
        """
        # Null check GROUPS:
        if common.GROUPS is None:
            error: str = "Groups not loaded."
            raise GroupError(error)
        return iter(common.GROUPS)

    ##############################
    # Properties:
    ##############################
    @property
    def is_loaded(self) -> bool:
        """
        Return if this has been loaded somehow.
        :return: Bool.
        """
        return common.GROUPS is not None

    @property
    def last_fetched(self) -> datetime:
        """
        The date / time this was last retrieved from papertrail, time in UTC.
        :return: Datetime object.
        """
        return common.GROUPS_LAST_FETCHED

    @property
    def groups(self) -> tuple[Group]:
        """
        Return a tuple of groups.
        :return: Tuple[Group]
        """
        return tuple(common.GROUPS)


########################################################################################################################
# TEST CODE:
########################################################################################################################
if __name__ == '__main__':
    from Systems import Systems
    from apiKey import API_KEY
    test_systems = Systems(api_key=API_KEY)
    test_groups = Groups(api_key=API_KEY)
    for test_group in test_groups:
        print("ID:", test_group.id, "Name:", test_group.name)

    test_reload: bool = False
    test_create: bool = False
    test_update: bool = False
    test_delete: bool = False

    if test_reload:

        print("Init time:", test_groups.groups[0].last_fetched.isoformat())
        test_groups.groups[0].reload()
        print("reload time:", test_groups.groups[0].last_fetched.isoformat())

    if test_create:
        print("Adding TEST group.")
        new_group = test_groups.create(name="TEST")
        print("New group: ", new_group.name)

    if test_update:
        print("Updating TEST group.")
        test_groups['TEST'].update(system_wildcard='*prod*')
        print("Updated.")

    if test_delete:
        print("Deleting TEST:")
        test_groups.delete('TEST')
        print("Group Deleted.")
