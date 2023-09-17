#!/usr/bin/env python3
"""
    File: Users.py
"""
from typing import Optional, Iterator
from datetime import datetime
from warnings import warn
try:
    from common import USE_WARNINGS, BASE_URL, __type_error__, requests_get, requests_del, requests_post, convert_to_utc
    import common
    from Exceptions import UsersError, PapertrailWarning, ParameterError
    from User import User
    from Group import Group
    from Groups import Groups
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import USE_WARNINGS, BASE_URL, __type_error__, requests_get, requests_del, requests_post, convert_to_utc
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import UsersError, PapertrailWarning, ParameterError
    from PyPapertrail.User import User
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
            Self = TypeVar("Self", bound="Groups")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)


class Users(object):
    """
    Class to store users list.
    """
##########################
# Initialize:
##########################
    def __init__(self,
                 api_key: str,
                 from_dict: Optional[dict] = None,
                 do_load: bool = True,
                 ) -> None:
        """
        Initialize users' list.
        :param api_key: Str: The api key
        :param from_dict: Dict: The dict provided by __to_dict__(), NOTE: If from_dict is provided, do_load is ignored.
        :param do_load: Bool: Load from Papertrail or not. Default = True.
        """
        # Type check:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        elif not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)

        # Store api key:
        self._api_key: str = api_key
        # Store a 'Groups' instance:
        self._groups: Groups = Groups(api_key=api_key, do_load=False)
        # Load this instance:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif do_load:
            self.load()
        return

#########################
# To / from Dict:
#########################
    def __from_dict__(self, from_dict) -> None:
        """
        Load from a dict created by __to_dict__()
        :param from_dict: Dict: The dict to load from
        :raises UsersError: If invalid dict provided.
        :return: None
        """
        try:
            common.USERS_LAST_FETCHED = None
            if from_dict['last_fetched'] is not None:
                common.USERS_LAST_FETCHED = datetime.fromisoformat(from_dict['last_fetched'])
            common.USERS = []
            for user_dict in from_dict['_users']:
                user = User(api_key=self._api_key, from_dict=user_dict)
                common.USERS.append(user)
        except (KeyError, ValueError):
            error: str = "Invalid dict provided to __from_dict__()"
            raise UsersError(error)
        return

    @staticmethod
    def __to_dict__() -> dict:
        """
        Return a json / pickle friendly dict.
        :return: Dict
        """
        return_dict: dict = {
            'last_fetched': None,
            '_users': None,
        }
        if common.USERS_LAST_FETCHED is not None:
            return_dict['last_fetched'] = common.USERS_LAST_FETCHED.isoformat()
        if common.USERS is not None:
            return_dict['_users'] = []
            for user in common.USERS:
                user_dict = user.__to_dict__()
                return_dict['_users'].append(user_dict)
        return return_dict

##########################
# Methods:
##########################
    def load(self) -> None:
        """
        Load data from papertrail.
        :return: None
        """
        # Build url:
        list_url: str = BASE_URL + 'users.json'
        # Make the request:
        response: list[dict] = requests_get(url=list_url, api_key=self._api_key)
        # Parse the response:
        common.USERS = []
        for raw_user in response:
            user = User(api_key=self._api_key, raw_user=raw_user)
            common.USERS.append(user)
        common.USERS_LAST_FETCHED = convert_to_utc(datetime.utcnow())
        return

    def reload(self) -> None:
        """
        Reload the data.
        :return: None
        """
        return self.load()

    def invite(self,
               email: str,
               read_only: bool,
               manage_members: Optional[bool] = None,
               manage_billing: Optional[bool] = None,
               purge_logs: Optional[bool] = None,
               all_groups: Optional[bool] = None,
               groups: Optional[list[Group | int | str]] = None,
               ) -> None:
        """
        Invite a user to your papertrail account.
        :param email: Str: Email address to send invite to.
        :param read_only: Bool: Is the user read only?
        :param manage_members: Optional[bool]: Can the user manage members?
        :param manage_billing: Optional[bool]: Can the user manage billing?
        :param purge_logs: Optional[bool]: Can the user delete logs?
        :param all_groups: Optional[bool]: Can the user see all the groups?
        :param groups: Optional[list[Group | int | str]]: List of groups the user should see.  Elements should be one
            of: Group objects, str [group name], or int[group id].
        :raises TypeError: If an invalid type passed.
        :raises UsersError: If an invalid parameter situation is encountered.
        :raise IndexError: If an invalid group, group id, or group name is found in the loaded Groups.
        :return: None
        """
        # Type check:
        if not isinstance(email, str):
            __type_error__("email", "str", email)
        elif not isinstance(read_only, bool):
            __type_error__("read_only", "bool", read_only)
        elif manage_billing is not None and not isinstance(manage_billing, bool):
            __type_error__("manage_billing", "Optional[bool]", manage_billing)
        elif manage_members is not None and not isinstance(manage_members, bool):
            __type_error__("manage_members", "Optional[bool]", manage_members)
        elif purge_logs is not None and not isinstance(purge_logs, bool):
            __type_error__("purge_logs", "Optional[bool]", purge_logs)
        elif all_groups is not None and not isinstance(all_groups, bool):
            __type_error__("all_groups", "Optional[bool]", all_groups)
        elif groups is not None and not isinstance(groups, list):
            __type_error__("all_groups", "Optional[list[Group | int | str]]", groups)
        # Type check groups elements:
        if groups is not None:
            for i, element in enumerate(groups):
                if not isinstance(element, Group) and not isinstance(element, str) and not isinstance(element, int):
                    __type_error__("groups[%i]" % i, "Group | str | int", groups[i])
        # Parameter check that groups is not an empty list:
        if groups is not None and len(groups) == 0:
            error: str = "Parameter error, groups cannot be an empty list."
            raise ParameterError(error)
        # Parameter check groups and all groups together:
        if all_groups and groups is not None:
            error: str = "Parameter error, if all_groups is True, then groups must be None."
            raise ParameterError(error)
        # Build invite url:
        invite_url: str = BASE_URL + 'users/invite.json'
        # Build json data:
        json_data: dict = {'user': {
            'email': email,
            'read_only': read_only,
        }}
        if manage_members is not None:
            json_data['user']['manage_members'] = manage_members
        if manage_billing is not None:
            json_data['user']['manage_billing'] = manage_billing
        if purge_logs is not None:
            json_data['user']['purge_logs'] = purge_logs
        if all_groups is not None:
            json_data['user']['can_access_all_groups'] = all_groups
        if groups is not None:
            # Load groups if not already loaded:
            if not self._groups.is_loaded:
                if USE_WARNINGS:
                    warning: str = "Loading groups from Papertrail."
                    warn(warning, PapertrailWarning)
                self._groups.load()
            # Get a list of verified group id's:
            group_ids: list[int] = []
            for unknown_group in groups:
                if isinstance(unknown_group, Group):
                    if unknown_group not in self._groups:
                        error: str = "Unknown Group object passed."
                        IndexError(error)
                    group_ids.append(unknown_group.id)
                elif isinstance(unknown_group, int):
                    group = self._groups[unknown_group]  # Raises IndexError if not found.
                    group_ids.append(group.id)
                elif isinstance(unknown_group, str):
                    group = self._groups[unknown_group]  # Raises IndexError if not Found.
                    group_ids.append(group.id)
            # Add the group id's to JSON data:
            json_data['user']['group_ids'] = group_ids
        # Make the request:
        requests_post(url=invite_url, api_key=self._api_key, json_data=json_data, returns_json=False)
        return

    def delete(self, user_to_del: User | str | int) -> Self:
        """
        Delete a given user, returns the updated users object.
        :param user_to_del: User object | str | int: The user to delete, either a User object, the email of the
            user(str), or the user id(int).
        :raises IndexError: If the user is not found.
        :return: Users: The updated Self object.
        """
        # Type check:
        if not isinstance(user_to_del, User) and not isinstance(user_to_del, str) and not isinstance(user_to_del, int):
            __type_error__("user_to_del", "User | str | int", user_to_del)
        # Get the user id to delete:
        user_id_to_del: int | User = -1
        if isinstance(user_to_del, User):
            if user_to_del not in self:
                error: str = "Provided User object not found."
                raise IndexError(error)
            user_id_to_del = user_to_del.id
        elif isinstance(user_to_del, str) or isinstance(user_to_del, int):
            user = self[user_to_del]  # Raises index error if not found.
            user_to_del = user
            user_id_to_del = user.id
        # Build the delete url:
        delete_url: str = BASE_URL + "users/%i.json" % user_id_to_del
        # Make the request, returns Nothing:
        requests_del(url=delete_url, api_key=self._api_key, returns_json=False)
        common.USERS.remove(user_to_del)
        return self

############################
# Getters:
############################
    @staticmethod
    def get_by_id(search_id: int) -> Optional[User]:
        """
        Get a user by ID, returns None if not found.
        :param search_id: Int: The ID of the user.
        :raises UsersError: If the user list has not been loaded.
        :return: Optional[User]
        """
        # Type checks:
        if not isinstance(search_id, int):
            __type_error__("search_id", "int", search_id)
        # Null check USERS:
        if common.USERS is None:
            error: str = "Users has not been loaded."
            raise UsersError(error)
        # Search users:
        for user in common.USERS:
            if user.id == search_id:
                return user
        return None

    @staticmethod
    def get_by_email(search_email: str) -> Optional[User]:
        """
        Get a user by email returns None if not found.
        :param search_email: Str: The email to search for.
        :raises UsersError: If the user list has not been loaded.
        :return: Optional[User]
        """
        # Type check:
        if not isinstance(search_email, str):
            __type_error__("search_email", "str", search_email)
        # Null check USERS:
        if common.USERS is None:
            error: str = "Users has not been loaded."
            raise UsersError(error)
        # Search users:
        for user in common.USERS:
            if user.email == search_email:
                return user
        return None

############################
# Overrides:
############################
    def __getitem__(self, item: int | str) -> User:
        """
        Allow indexing by square brackets.
        :param item: Int | str: The index to select, can be an int for the user ID, a str for the email.
        :raises UsersError: If the user list hasn't been loaded.
        :return: User
        """
        # Null check USERS:
        if common.USERS is None:
            error: str = "Users not loaded."
            raise UsersError(error)
        # Select type:
        if isinstance(item, int):
            for user in common.USERS:
                if user.id == item:
                    return user
        elif isinstance(item, str):
            for user in common.USERS:
                if user.email == item:
                    return user
        error: str = "Can only index by int, str, or slice of int."
        raise TypeError(error)

    def __iter__(self) -> Iterator[User]:
        """
        Get an iterator of users
        :raises: UsersError: If the user list hasn't been loaded.
        :return: Iterator
        """
        # Null check USERS:
        if common.USERS is None:
            error: str = "Users not loaded."
            raise UsersError(error)
        # return iterator:
        return iter(common.USERS)

    def __len__(self) -> int:
        """
        Len is the number of users.
        :raises: UsersError: If the user list hasn't been loaded.
        :return: Int
        """
        # Null check USERS:
        if common.USERS is None:
            error: str = "Users not loaded."
            raise UsersError(error)
        return len(common.USERS)

############################
# Properties:
############################
    @property
    def is_loaded(self) -> bool:
        """
        Is the data loaded?
        :return: Bool
        """
        return common.USERS is not None

    @property
    def last_fetched(self) -> Optional[datetime]:
        """
        Last time this was loaded from papertrail in UTC.
        :return: Datetime
        """
        return common.USERS_LAST_FETCHED

    @property
    def users(self) -> tuple[User]:
        """
        Return a tuple of the Users.
        :return: Tuple(User)
        """
        return tuple(common.USERS)


########################################################################################################################
# TEST CODE:
########################################################################################################################
if __name__ == '__main__':
    from apiKey import API_KEY
    users = Users(api_key=API_KEY)

    exit(0)
