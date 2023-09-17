#!/usr/bin/env python3
"""
    File: User.py
"""
from typing import Optional
from warnings import warn
try:
    from common import USE_WARNINGS, BASE_URL, __type_error__, requests_put
    import common
    from Exceptions import UsersError, InvalidServerResponse, PapertrailWarning, ParameterError
    from Groups import Groups
    from Group import Group
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import USE_WARNINGS, BASE_URL, __type_error__, requests_put
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import UsersError, InvalidServerResponse, PapertrailWarning, ParameterError
    from PyPapertrail.Groups import Groups
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
            Self = TypeVar("Self", bound="Groups")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)


class User(object):
    """
    Class to store a single user.
    """
    def __init__(self,
                 api_key: str,
                 from_dict: Optional[dict] = None,
                 raw_user: Optional[dict] = None,
                 ) -> None:
        """
        Initialize a user.
        :param api_key: Str: Api key.
        :param from_dict: Dict: A dict provided by __to_dict__().
        :param raw_user: Dict: Raw dict provided by Papertrail.
        """
        # Type checks:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        elif raw_user is not None and not isinstance(raw_user, dict):
            __type_error__("raw_user", "Optional[dict]", raw_user)

        # Parameter checks:
        if (from_dict is None and raw_user is None) or (from_dict is not None and raw_user is not None):
            error: str = "ParameterError: Either from_dict or raw_user must be defined, but not both."
            raise ParameterError(error)

        # Store api key:
        self._api_key = api_key

        # Set properties:
        self._id: int = -1
        self._email: str = ''
        self._groups: Groups = Groups(api_key=api_key, do_load=False)

        # Load this instance:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif raw_user is not None:
            self.__from_raw_user__(raw_user)
        return

#####################
# To / From dict, and from raw user:
#####################
    def __from_dict__(self, from_dict: dict) -> None:
        try:
            self._id = from_dict['id']
            self._email = from_dict['email']
        except KeyError:
            error: str = "Invalid dict provided to __from_dict__"
            raise UsersError(error)
        return

    def __to_dict__(self) -> dict:
        return_dict: dict = {
            'id': self._id,
            'email': self._email,
        }
        return return_dict

    def __from_raw_user__(self, raw_user: dict) -> None:
        try:
            self._id = raw_user['id']
            self._email = raw_user['email']
        except KeyError:
            error: str = "KeyError while parsing papertrail response."
            raise InvalidServerResponse(error)
        return

###############################
# Methods:
###############################
    def update(self,
               email: Optional[str] = None,
               read_only: Optional[bool] = None,
               manage_members: Optional[bool] = None,
               manage_billing: Optional[bool] = None,
               purge_logs: Optional[bool] = None,
               all_groups: Optional[bool] = None,
               groups: Optional[list[Group | int | str]] = None,
               ) -> Self:
        """
        Update this user, NOTE: one of the parameters must be defined.
        :param email: Optional[str]: The users' email address.
        :param read_only: Optional[bool]: User is read only.
        :param manage_members: Optional[bool]: User can manage members.
        :param manage_billing: Optional[bool]: User can manage billing.
        :param purge_logs: Optional[bool]: User can delete logs.
        :param all_groups: Optional[bool]: User can access all groups.
        :param groups: Optional[list[Group | int | str]]: List of Group objects, group id's[int], or group names[str]
        :return: User: The updated instance.
        """
        # Type check:
        if email is not None and not isinstance(email, str):
            __type_error__("email", "Optional[str]", email)
        elif read_only is not None and not isinstance(read_only, bool):
            __type_error__("read_only", "Optional[bool]", read_only)
        elif manage_members is not None and not isinstance(manage_members, bool):
            __type_error__("manage_members", "Optional[bool]", manage_members)
        elif manage_billing is not None and not isinstance(manage_billing, bool):
            __type_error__("manage_billing", "Optional[bool]", manage_billing)
        elif purge_logs is not None and not isinstance(purge_logs, bool):
            __type_error__("purge_logs", "Optional[bool]", purge_logs)
        elif all_groups is not None and not isinstance(all_groups, bool):
            __type_error__("all_groups", "Optional[bool]", all_groups)
        elif groups is not None and not isinstance(groups, list):
            __type_error__("groups", "list[Group | str | int]", groups)
        # Type check groups elements:
        if groups is not None:
            for i, element in enumerate(groups):
                if not isinstance(element, Group) and not isinstance(element, str) and not isinstance(element, int):
                    __type_error__("groups[%i]" % i, "Group | str | int]", groups[i])
        # Check that groups isn't an empty list:
        if groups is not None and len(groups) == 0:
            error: str = "ParameterError: groups, if defined, cannot be an empty list."
            raise ParameterError(error)
        # Parameter check that at least one parameter is defined:
        all_none: bool = True
        for parameter in (email, read_only, manage_members, manage_billing, purge_logs, all_groups, groups):
            if parameter is not None:
                all_none = False
        if all_none:
            error: str = "ParameterError: At least one parameter must be defined."
            raise ParameterError(error)
        # Parameter check that if all_groups is True, groups are not defined:
        if all_groups and groups is not None:
            error: str = "ParameterError: If all_groups == True, groups must be None."
            raise ParameterError(error)
        # Build the update url:
        update_url: str = BASE_URL + 'users/%i.json' % self._id
        # Build the JSON data:
        json_data: dict = {'user': {}}
        if email is not None:
            json_data['user']['email'] = email
        if read_only is not None:
            json_data['user']['read_only'] = read_only
        if manage_members is not None:
            json_data['user']['manage_members'] = manage_members
        if manage_billing is not None:
            json_data['user']['manage_billing'] = manage_billing
        if purge_logs is not None:
            json_data['user']['purge_logs'] = purge_logs
        if all_groups is not None:
            json_data['user']['can_access_all_groups'] = all_groups
        if groups is not None:
            # Load groups to validate groups elements:
            if not self._groups.is_loaded:
                if USE_WARNINGS:
                    warning: str = "Loading groups from Papertrail."
                    warn(warning, PapertrailWarning)
                self._groups.load()
            # Get a list of group id's:
            group_ids: list[int] = []
            for unknown_group in groups:
                if isinstance(unknown_group, Group):
                    if unknown_group not in self._groups:
                        error: str = "IndexError: Group object not found."
                        raise IndexError(error)
                    group_ids.append(unknown_group.id)
                elif isinstance(unknown_group, int) or isinstance(unknown_group, str):
                    group = self._groups[unknown_group]  # Raises IndexError if not found.
                    group_ids.append(group.id)
            # Add group id's to JSON data.
            json_data['user']['group_ids'] = group_ids

        # Make the request, note request doesn't produce JSON.
        requests_put(url=update_url, api_key=self._api_key, json_data=json_data, returns_json=False)
        return

###############################
# Overrides:
###############################
    def __str__(self) -> str:
        """
        Refer as a string, get the email address.
        :return: Str
        """
        return self._email

    def __int__(self) -> int:
        """
        Refer as integer, get the user id.
        :return: Int
        """
        return self._id

###############################
# Properties:
###############################
    @property
    def id(self) -> int:
        """
        Return the user id.
        :return: Int
        """
        return self._id

    @property
    def email(self) -> str:
        """
        Users' email address.
        :return: Str
        """
        return self._email


# ########################################################################################################################
# # TEST CODE:
# ########################################################################################################################
# if __name__ == '__main__':
#     from apiKey import API_KEY
#
#     exit(0)
