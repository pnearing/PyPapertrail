#!/usr/bin/env python3
"""
    File: Archives.py
"""
from typing import Optional, Iterator, Any
from datetime import datetime
try:
    from common import BASE_URL, __type_error__, convert_to_utc, requests_get
    import common
    from Exceptions import ArchiveError
    from Archive import Archive
except (ModuleNotFoundError, ImportError):
    from PyPapertrail.common import BASE_URL, __type_error__, convert_to_utc, requests_get
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import ArchiveError
    from PyPapertrail.Archive import Archive

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

            Self = TypeVar("Self", bound="Archives")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)


class Archives(object):
    """Class to hold papertrail archive calls."""
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
        # Type Check:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        elif not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)
        # Store api key:
        self._api_key = api_key
        # Load this instance:
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
        try:
            common.ARCHIVES_LAST_FETCHED = None
            if from_dict['last_fetched'] is not None:
                common.ARCHIVES_LAST_FETCHED = datetime.fromisoformat(from_dict['last_fetched'])
            common.ARCHIVES = []
            for archive_dict in from_dict['_archives']:
                archive = Archive(api_key=self._api_key, from_dict=archive_dict)
                common.ARCHIVES.append(archive)
        except (KeyError, ValueError) as e:
            error: str = "Invalid dict passed to __from_dict__()"
            raise ArchiveError(error, exception=e)
        return

    @staticmethod
    def __to_dict__() -> dict:
        """
        Create a json / pickle friendly dict containing all the archives.
        :return: Dict.
        """
        return_dict = {
            'last_fetched': None,
            '_archives': None,
        }
        if common.ARCHIVES_LAST_FETCHED is not None:
            return_dict['last_fetched'] = common.ARCHIVES_LAST_FETCHED.isoformat()
        if common.ARCHIVES is not None:
            return_dict['_archives'] = []
            for archive in common.ARCHIVES:
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
        common.ARCHIVES = []
        common.ARCHIVES_LAST_FETCHED = convert_to_utc(datetime.utcnow())
        for raw_archive in response:
            archive = Archive(api_key=self._api_key, raw_archive=raw_archive, last_fetched=common.ARCHIVES_LAST_FETCHED)
            common.ARCHIVES.append(archive)
        return

    def reload(self) -> None:
        """
        Reload the data from Papertrail.
        :return: None
        """
        return self.load()

######################################
# Getters:
######################################
    @staticmethod
    def get_by_file_name(search_file_name: str) -> Archive | None:
        """
        Return an archive with a matching filename.
        :param search_file_name: Str: The file name to search for.
        :return: Archive | None
        """
        # type check:
        if not isinstance(search_file_name, str):
            __type_error__("search_file_name", "str", search_file_name)
        # Null check ARCHIVES:
        if common.ARCHIVES is None:
            error: str = "Archives not loaded."
            raise ArchiveError(error)
        # Search archives:
        for archive in common.ARCHIVES:
            if archive.file_name == search_file_name:
                return archive
        return None

    @staticmethod
    def get_by_start_time(search_start_time: datetime) -> Archive | None:
        """
        Return an archive matching a given start_time, given time will be converted to UTC if timezone aware or assumed
            to be un UTC if timezone naive.
        :param search_start_time: Datetime object: Datetime to search for.
        :return: Archive | None
        """
        # type check:
        if not isinstance(search_start_time, datetime):
            __type_error__("search_start_time", "datetime", search_start_time)
        # Null check ARCHIVES:
        if common.ARCHIVES is None:
            error: str = "Archives not loaded."
            raise ArchiveError(error)
        # Search archives:
        search_start_time = convert_to_utc(search_start_time)
        for archive in common.ARCHIVES:
            if archive.start_time == search_start_time:
                return archive
        return None

    @staticmethod
    def get_by_end_time(search_end_time: datetime) -> Archive | None:
        """
        Get an archive matching a given stop time. Given time will be converted to UTC if timezone aware or assumed to
            be UTC if timezone naive.
        :param search_end_time: Datetime object: Datetime to search for.
        :return: Archive | None
        """
        # Type check:
        if not isinstance(search_end_time, datetime):
            __type_error__("search_stop_time", "datetime", search_end_time)
        # Null check ARCHIVES:
        if common.ARCHIVES is None:
            error: str = "Archives not loaded."
            raise ArchiveError(error)
        # Search archives:
        search_end_time = convert_to_utc(search_end_time)
        for archive in common.ARCHIVES:
            if archive.end_time == search_end_time:
                return archive
        return None

    @staticmethod
    def get_by_time(search_time: datetime) -> Optional[Archive]:
        """
        Get an archive that contains a given datetime object, matches start_time <= search_time <= end_time.
        :param search_time: Datetime object: The datetime to search for.
        :raises ArchiveError: If archives have not been loaded.
        :return: Optional[Archive]
        """
        # type check:
        if not isinstance(search_time, datetime):
            __type_error__("search_time", "datetime", search_time)
        # Null check ARCHIVES:
        if common.ARCHIVES is None:
            error: str = "Archives not loaded."
            raise ArchiveError(error)
        # Search archives:
        search_time = convert_to_utc(search_time)
        for archive in common.ARCHIVES:
            if archive.start_time <= search_time <= archive.end_time:
                return archive
        return None

######################################
# Overrides:
######################################

    def __getitem__(self, item: datetime | int | str | slice) -> Archive | list[Archive]:
        """
        Get an archive, use a datetime object to search by date/time. Timezone-aware datetime objects will be converted
         to UTC before indexing. Timezone-unaware datetime objects are assumed to be in UTC. Use an int to index as a
         list, and a str to search by file_name. Use a slice of datetime objects to slice by dates, note: Slicing by
         datetime objects with a step parameter are currently not supported.
        :param item: Datetime | int | str | slice: Index / Slice to search by.
        :raises: IndexError: Index error if item is not found.
        :raises: TypeError: If item is not of type datetime, int, str, or slice of ints / datetime objects.
        :raises: ArchivesError: If the archive list hasn't been loaded yet.
        :returns: Archive | list[Archive]
        """
        # Null check ARCHIVES:
        if common.ARCHIVES is None:
            error: str = "Archives not loaded."
            raise ArchiveError(error)
        # Select TYPE:
        if isinstance(item, datetime):
            search_date: datetime = convert_to_utc(item)
            search_date.replace(microsecond=0)
            for archive in common.ARCHIVES:
                if archive.start_time == search_date:
                    return archive
                raise IndexError()
        elif isinstance(item, int):
            return common.ARCHIVES[item]
        elif isinstance(item, str):
            for archive in common.ARCHIVES:
                if archive.file_name == item:
                    return archive
            raise IndexError()
        elif isinstance(item, slice):
            error: str = ("When slicing, start must be a datetime object that is less than stop, which also must be a "
                          "datetime object. Step must be None.")
            # Type check:
            if not isinstance(item.start, datetime):
                raise TypeError(error)
            elif item.stop is not None and not isinstance(item.stop, datetime):
                raise TypeError(error)
            elif item.step is not None:
                raise TypeError(error)
            elif item.stop is not None and (item.start > item.stop):
                raise TypeError(error)
            # Do Slice:
            return_list: list[Archive] = []
            slice_start: datetime = convert_to_utc(item.start)
            if item.stop is None:
                for archive in common.ARCHIVES:
                    if archive.start_time >= slice_start:
                        return_list.append(archive)
                return return_list
            else:
                slice_stop = convert_to_utc(item.stop)
                for archive in common.ARCHIVES:
                    if slice_start <= archive.start_time < slice_stop:
                        return_list.append(archive)
                return return_list
        error: str = "Can only index by a datetime object, an int, a str, or a slice of datetime objects."
        raise TypeError(error)

    def __iter__(self) -> Iterator[Archive]:
        """
        Get an iterator of all the archives.
        :raises: ArchiveError: If the archive list hasn't been loaded.
        :return: Iterator[Archive]
        """
        # Null check archives:
        if common.ARCHIVES is None:
            error: str = "Archives not loaded."
            raise ArchiveError(error)
        # Return iterator:
        return iter(common.ARCHIVES)

    def __len__(self) -> int:
        """
        Return the number of archives:
        :raises: ArchiveError: If the archive list hasn't been loaded.
        :return: Int
        """
        # Null check archives:
        if common.ARCHIVES is None:
            error: str = "Archives not loaded."
            raise ArchiveError(error)
        # Return len:
        return len(common.ARCHIVES)

    ##################################
    # Properties:
    ##################################
    @property
    def last_fetched(self) -> Optional[datetime]:
        """
        Time the archive list was last fetched from papertrail.
        :return: Optional[datetime]: Timezone-aware datetime object in UTC.
        """
        return common.ARCHIVES_LAST_FETCHED

    @property
    def is_loaded(self) -> bool:
        """
        Is the archive list loaded?
        :return: Bool.
        """
        return common.ARCHIVES is not None

    @property
    def archives(self) -> tuple[Archive]:
        """
        Return a tuple of archives.
        :return: Tuple[Archive]
        """
        return tuple(common.ARCHIVES)

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
