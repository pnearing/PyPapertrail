#!/usr/bin/env python3
import sys
if sys.version_info.major != 3 or sys.version_info.minor < 10:
    print("Only python >= 3.10 supported")
    exit(128)
# Define Self:
try:
    from typing import Self
except ImportError:
    try:
        from typing_extensions import Self
    except (ModuleNotFoundError, ImportError):
        try:
            from typing import TypeVar
            Self = TypeVar("Self", bound="Archives")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)
from typing import Optional, Iterator, Any
from datetime import datetime, timezone
from common import BASE_URL, is_timezone_aware, __type_error__, __raise_for_http_error__, requests_get
from Exceptions import ArchiveError
from Archive import Archive


class Archives(object):
    """Class to hold papertrail archive calls."""
    _ARCHIVES: list[Archive] = []
    _IS_LOADED: bool = False
    _LAST_FETCHED: Optional[datetime] = None

#########################################
# Initialize:
#########################################
    def __init__(self,
                 api_key: str,
                 from_dict: Optional[dict] = None,
                 do_load: bool = True,
                 ) -> None:
        """
        Initialize Papertrail API.
        :param api_key: Str: The papertrail "API Token" found in papertrail under: settings / profile / API Token
        :param from_dict: Dict: Load from a dict created by __to_dict__().
            NOTE: If not set to None, it will ignore do_load.
        :param do_load: Bool: Load the archive list on initialization.
            Default = True.
        :raises: ArchiveError: Raises ArchiveError on error during loading.
        :returns: None
        """
        # Store api key:
        self._api_key = api_key

        if from_dict is not None:
            if not isinstance(from_dict, dict):
                __type_error__("from_dict", "dict", from_dict)
            self.__from_dict__(from_dict)
        elif do_load:
            self.load()
        return

#####################################
# Load / save functions:
#####################################
    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load the archive list from a dict created by __to_dict__().
        :param from_dict: Dict: The dict to load from.
        :return: None
        """
        self._LAST_FETCHED = None
        if from_dict['last_fetched'] is not None:
            self._LAST_FETCHED = datetime.fromisoformat(from_dict['last_fetched']).replace(tzinfo=timezone.utc)
        self._ARCHIVES = []
        for archive_dict in from_dict['_archives']:
            archive = Archive(api_key=self._api_key, from_dict=archive_dict)
            self._ARCHIVES.append(archive)
        self._IS_LOADED = True
        return

    def __to_dict__(self) -> dict:
        """
        Create a json / pickle friendly dict containing all the archives.
        :return: Dict.
        """
        return_dict = {
            'last_fetched': None,
            '_archives': [],
        }
        if self._LAST_FETCHED is not None:
            return_dict['last_fetched'] = self._LAST_FETCHED.isoformat()
        for archive in self._ARCHIVES:
            archive_dict = archive.__to_dict__()
            return_dict['_archives'].append(archive_dict)
        return return_dict

#################################################
# Methods:
#################################################
    def load(self) -> None:
        """
        Load the archive list from server.
        :return: Tuple[bool, str]: First element, the bool, is True if successful, and False if not, if the first
                    element is True, the second element, the str is the message: "OK"; And if the first element is
                    False, the second element will be an error message.
        """
        # Generate list url:
        list_url = BASE_URL + 'archives.json'
        response = requests_get(list_url, self._api_key)
        # Return the list as list of Archive objects:
        self._ARCHIVES = []
        self._LAST_FETCHED: datetime = datetime.utcnow().replace(tzinfo=timezone.utc)
        for raw_archive in response:
            archive = Archive(api_key=self._api_key, raw_archive=raw_archive, last_fetched=self._LAST_FETCHED)
            self._ARCHIVES.append(archive)
        # Set variables:
        self._IS_LOADED = True
        return

######################################
# List like overrides.
######################################

    def __getitem__(self, item: datetime | int | str | slice) -> Archive | list[Archive]:
        """
        Get an archive, use a datetime object to search by date/time. Timezone-aware datetime objects will be converted
         to UTC before indexing. Timezone-unaware datetime objects are assumed to be in UTC. Use an int to index as a
         list, and a str to search by file_name, use a slice of ints to obtain a slice. Use a slice of datetime objects
         to slice by dates.
        :param item: Datetime | int | str | slice: Index / Slice to search by.
        :raises: IndexError | TypeError. Index error if item is not found, TypeError if item is not of type datetime,
                    int, str, or slice of ints / datetime objects.
        :returns: Archive
        """
        if isinstance(item, datetime):
            if is_timezone_aware(item):
                # Convert to utc
                search_date = item.astimezone(timezone.utc)
            else:
                # Make timezone aware, assuming the time is in UTC:
                item.replace(tzinfo=timezone.utc)
                search_date = item
            for archive in self._ARCHIVES:
                if archive.start_time == search_date:
                    return archive
                raise IndexError()
        elif isinstance(item, int):
            return self._ARCHIVES[item]
        elif isinstance(item, str):
            for archive in self._ARCHIVES:
                if archive.file_name == item:
                    return archive
            raise IndexError()
        elif isinstance(item, slice):
            if isinstance(item.start, int):
                return self._ARCHIVES[item]
            elif isinstance(item.start, datetime):
                if item.step is not None:
                    # TODO: Slice with step parameter.
                    raise NotImplementedError("Step not implemented when using datetime objects to slice.")
                elif item.start > item.stop:
                    # TODO: Support reverse slices, when step is negative.
                    raise NotImplementedError("Reverse slices not implemented when using datetime objects to slice.")
                return_list: list[Archive] = []
                for archive in self._ARCHIVES:
                    if item.start <= archive.start_time < item.stop:
                        return_list.append(archive)
                return return_list
            else:
                raise TypeError()
        else:
            raise TypeError()

    def __iter__(self) -> Iterator[Archive]:
        """
        Get an iterator of all the archives.
        :return: Iterator[Archive]
        """
        return iter(self._ARCHIVES)

    def __len__(self) -> int:
        """
        Return the number of archives:
        :return: int
        """
        return len(self._ARCHIVES)

##################################
# Properties:
##################################
    @property
    def last_fetched(self) -> Optional[datetime]:
        """
        Time the archive list was last fetched from papertrail.
        :return: Optional[datetime]: Timezone-aware datetime object in UTC.
        """
        return self._LAST_FETCHED

    @property
    def is_loaded(self) -> bool:
        """
        Is the archive list loaded?
        :return: Bool.
        """
        return self._IS_LOADED


########################################################################################################################
# Test code:
########################################################################################################################


def download_callback(archive: Archive, bytes_downloaded: int, argument: Any):
    from time import sleep
    print("\r", end='')
    print("Downloading archive: %s... %i bytes" % (archive.file_name, bytes_downloaded), end='')
    if argument is not None:
        print(str(argument), end='')
    sleep(0.25)
    return


if __name__ == '__main__':
    from apiKey import API_KEY
    import os

    print("Fetching archive list...")
    archives = Archives(API_KEY)

    home_dir = os.environ.get("HOME")

    test_list: bool = True
    test_download: bool = True

    # Test list:
    if test_list:
        for test_archive in archives:
            print(test_archive.file_name)

    if test_download:
        # Download the latest archive, overwriting if exists.
        test_archive = archives[-1]
        print("Downloading archive: %s" % test_archive.file_name, end='')
        test_archive.download(destination_dir=home_dir, overwrite=True, callback=download_callback)
        print()
    exit(0)
