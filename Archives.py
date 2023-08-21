#!/usr/bin/env python3

from typing import Optional, Callable, Iterator
import os
import requests
from datetime import datetime, timezone
from common import BASE_URL, is_timezone_aware, __type_error__, __raise_for_http_error__
from Exceptions import ArchiveError, RequestReadTimeout


class Archive(object):
    """
    Class representing a Papertrail archive.
    """
###########################################
# Initialize:
###########################################
    def __init__(self,
                 api_key: str,
                 raw_archive: Optional[dict] = None,
                 from_dict: Optional[dict] = None,
                 ) -> None:
        """
        Initialize the archive.
        :param api_key: Str: The api key.
        :param raw_archive: Optional[dict]: The raw dict from papertrail listing. Default = None
        :param from_dict: Optional[dict]: Load from a saved dict created by __to_dict__().
        :return: None
        """
        # Type checks:
        if not isinstance(api_key, str):
            __type_error__("api_key","str", api_key)
        elif raw_archive is not None and not isinstance(raw_archive, dict):
            __type_error__("raw_archive", "dict", raw_archive)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        # Store api key:
        self._api_key: str = api_key

        # Define properties:
        self._start_time: datetime
        self._end_time: datetime
        self._formatted_start_time: str
        self._formatted_duration: str
        self._file_name: str
        self._file_size: int
        self._link: str
        self._duration: int
        self._is_downloaded: bool = False
        self._download_path: Optional[str] = None

        # Load archive properties:
        if raw_archive is None and from_dict is None:
            error: str = "Either raw_archive or from_dict must be defined, but not both."
            raise ArchiveError(error)
        elif raw_archive is not None and from_dict is not None:
            error: str = "Either raw_archive or from_dict must be defined, but not both."
            raise ArchiveError(error)
        elif raw_archive is not None:
            self.__from_raw_archive__(raw_archive)
        else:
            self.__from_dict__(from_dict)
        # Store downloading properties:
        self._downloading: bool = False
        return

#########################################
# Load / Save functions:
#########################################
    def __from_raw_archive__(self, raw_archive: dict) -> None:
        """
        Load the properties from the raw archive dict received from papertrail.
        :param raw_archive: Dict: The raw response dict from papertrail.
        :raises: ArchiveError: On key error.
        :return: None
        """
        # Extract data from raw_archive dict:
        try:
            self._start_time = datetime.fromisoformat(raw_archive['start'][:-1]).replace(tzinfo=timezone.utc)
            self._end_time = datetime.fromisoformat(raw_archive['end'][:-1]).replace(tzinfo=timezone.utc)
            self._formatted_start_time = raw_archive['start_formatted']
            self._formatted_duration = raw_archive['duration_formatted']
            self._file_name = raw_archive['filename']
            self._file_size = raw_archive['filesize']
            self._link = raw_archive['_links']['download']['href']
            # Calculate duration in minutes:
            if self._formatted_duration.lower() == '1 hour':
                self._duration = 60  # One hour in minutes
            elif self._formatted_duration.lower() == '1 day':
                self._duration = 24 * 60  # One day in minutes.
            else:
                raise NotImplementedError("Unknown duration_formatted value.")
            # Set downloaded and download path, assume not downloaded.
            self._is_downloaded = False
            self._download_path = None
        except KeyError as e:
            error: str = "KeyError while extracting data from raw_archive. Maybe papertrail changed their response."
            raise ArchiveError(error, exception=e)
        return

    def __from_dict__(self, from_dict: dict) -> None:
        """
        Load the properties from a dict made by __to_dict__().
        :param from_dict: Dict: the dictionary to load from.
        :raises: ArchiveError: On key error.
        :return: None
        """
        try:
            self._start_time = datetime.fromisoformat(from_dict['start_time']).replace(tzinfo=timezone.utc)
            self._end_time = datetime.fromisoformat(from_dict['end_time']).replace(tzinfo=timezone.utc)
            self._formatted_start_time = from_dict['formatted_start_time']
            self._formatted_duration = from_dict['formatted_duration']
            self._file_name = from_dict['file_name']
            self._file_size = from_dict['file_size']
            self._link = from_dict['link']
            self._duration = from_dict['duration']
            self._is_downloaded = from_dict['is_downloaded']
            self._download_path = from_dict['download_path']
        except KeyError as e:
            error: str = "KeyError while extracting data from the from_dict dictionary."
            raise ArchiveError(error, exception=e)
        return

    def __to_dict__(self) -> dict:
        """
        Create a dict containing all the information in a json / pickle friendly format.
        :return: Dict.
        """
        return_dict: dict = {
            'start_time': self._start_time.isoformat(),
            'end_time': self._end_time.isoformat(),
            'formatted_start_time': self._formatted_start_time,
            'formatted_duration': self._formatted_duration,
            'file_name': self._file_name,
            'file_size': self._file_size,
            'link': self._link,
            'is_downloaded': self._is_downloaded,
            'download_path': self._download_path,
        }

        return return_dict

##################################
# Methods:
##################################
    def download(self,
                 destination_dir: str,
                 file_name: Optional[str] = None,
                 overwrite: bool = False,
                 callback: Optional[Callable] = None,
                 argument: Optional[object] = None,
                 chunk_size: int = 8196,
                 ) -> tuple[bool, str | int, Optional[str]]:
        """
        Download this archive.
        :param destination_dir: Str. Directory to save file in.
        :param file_name: Optional[str]. Override the default file name with this file name. Default=None
        :param overwrite: Bool. Overwrite existing files. Default = False
        :param callback: Callable. The call back to call each chunk downloaded. Default = None.
                            The function signature is:
                            callback (archive: Archive, bytes_downloaded: int, argument: Optional[object])
        :param argument: Object. An optional argument to pass to the callback.  Default = None
        :param chunk_size: Int. The chunk size to download at a time in bytes. Default = 8196 (8K)
        :return: Tuple[bool, str | int, Optional[str]]: The first element is a status flag indicating success, True
                    being a success, and False a failure. If the first element is True, then the second element will be
                    the total number of bytes downloaded, and the third element will be the path to the downloaded file.
                    If the first element is False, the second element will be an error message indicating what went
                    wrong, and the third element will optionally be the path to the partially downloaded file.
        """
        # Type checks:
        if not isinstance(destination_dir, str):
            __type_error__("destination_dir", "str", destination_dir)
        elif file_name is not None and not isinstance(file_name, str):
            __type_error__("file_name", "str", file_name)
        elif not isinstance(overwrite, bool):
            __type_error__("overwrite", "bool", overwrite)
        elif callback is not None and not callable(callback):
            __type_error__("callback", "Callable", callback)
        elif not isinstance(chunk_size, int):
            __type_error__("chunk_size", "int", chunk_size)
        elif chunk_size < 1:
            raise ValueError("chunk_size must be greater than zero.")
        # Check to see if we're already downloading:
        if self._downloading:
            error: str = "Already downloading."
            raise ArchiveError(error)
        else:
            self._downloading = True
        # Validate destination:
        if not os.path.isdir(destination_dir):
            self._downloading = False
            error: str = "Destination: %s, is not a directory" % destination_dir
            raise ArchiveError(error, destination_dir=destination_dir)
        # Get the filename, and build the full download path.:
        if file_name is None:
            file_name = self._file_name
        download_path: str = os.path.join(destination_dir, file_name)
        # Check if the download path exists:
        if not overwrite and os.path.exists(download_path):
            self._downloading = False
            error: str = "Destination: %s, already exists." % download_path
            raise ArchiveError(error, download_path=download_path)
        # Open the file:
        try:
            file_handle = open(download_path, 'wb')
        except IOError as e:
            self._downloading = False
            error: str = "Failed to open '%s' for writing: %s" % (download_path, e.strerror)
            raise ArchiveError(error, exception=e, download_path=download_path)
        # Make the http request:
        headers = {"X-Papertrail-Token": self._api_key}
        try:
            r = requests.get(self._link, headers=headers, stream=True)
        except requests.ReadTimeout as e:
            raise RequestReadTimeout(url=self._link, exception=e)
        except requests.RequestException as e:
            message = "requests.RequestException: err_num=%i, strerror='%s'" % (e.errno, e.strerror)
            raise ArchiveError(message, exception=e)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            file_handle.close()
            self._downloading = False
            __raise_for_http_error__(request=r, exception=e)
        # Do the download:
        download_size: int = 0
        written_size: int = 0
        for chunk in r.iter_content(chunk_size):
            download_size += len(chunk)
            written_size += file_handle.write(chunk)
            if callback is not None:
                try:
                    callback(self, download_size, argument)
                except SystemExit as e:
                    raise e
                except Exception as e:
                    self._downloading = False
                    error: str = "Exception during callback execution."
                    raise ArchiveError(error, exception=e)
        # Download complete:
        file_handle.close()
        # Sanity checks for the download:
        if download_size != written_size:
            self._downloading = False
            error: str = "Downloaded bytes does not match written bytes. DL:%i != WR:%i" % (download_size, written_size)
            raise ArchiveError(
                error,
                download_path=download_path,
                downloaded_bytes=download_size,
                written_bytes=written_size
            )
        self._downloading = False
        self._is_downloaded = True
        self._download_path = download_path
        return True, download_size, download_path

##################################
# Properties:
##################################
    @property
    def start_time(self) -> datetime:
        """
        Start time of the archive.
        :return: Timezone-aware datetime object.
        """
        return self._start_time

    @property
    def end_time(self) -> datetime:
        """
        End time of the archive.
        :return: Timezone-aware datetime object.
        """
        return self._end_time

    @property
    def formatted_start_time(self) -> str:
        """
        Formatted start time.
        :return: English str.
        """
        return self._formatted_start_time

    @property
    def formatted_duration(self) -> str:
        """
        Formatted duration of the archive.
        :return: English str.
        """
        return self._formatted_duration

    @property
    def file_name(self) -> str:
        """
        File name of the archive.
        :return: Str
        """
        return self._file_name

    @property
    def file_size(self) -> int:
        """
        Size of the archive in bytes.
        :return: Int
        """
        return self._file_size

    @property
    def link(self) -> str:
        """
        Download link of the archive.
        :return: Str
        """
        return self._link

    @property
    def duration(self) -> int:
        """
        Duration of the archive in minutes.
        :return: Int
        """
        return self._duration

    @property
    def is_downloading(self) -> bool:
        """
        Is the archive currently downloading? True if downloading, False if not.
        :return: Bool
        """
        return self._downloading

    @property
    def is_downloaded(self) -> bool:
        """
        Has the archive been downloaded? True if so, False if not.
        :return: Bool
        """
        return self._is_downloaded

    @property
    def download_path(self) -> Optional[str]:
        """
        Path to the downloaded file if successfully downloaded. None if not downloaded.
        :return: Optional[str]
        """
        return self._download_path
########################################################################################################################
########################################################################################################################


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
                __type_error__("dict", from_dict)
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
        # Generate list url and headers:
        list_url = BASE_URL + 'archives.json'
        headers = {"X-Papertrail-Token": self._api_key}
        # Make the request:
        try:
            r: requests.Response = requests.get(list_url, headers=headers)
        except requests.ReadTimeout as e:
            raise RequestReadTimeout(url=list_url, exception=e)
        except requests.RequestException as e:
            error: str = "requests.RequestsException: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            raise ArchiveError(error, exception=e)
        # Check the response status.
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            __raise_for_http_error__(request=r, exception=e)
        # Parse the response:
        try:
            response = r.json()
        except requests.JSONDecodeError as e:
            error: str = "Server sent invalid json: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            raise ArchiveError(error, exception=e, request=r)
        # Return the list as list of Archive objects:
        self._ARCHIVES = []
        for raw_archive in response:
            archive = Archive(api_key=self._api_key, raw_archive=raw_archive)
            self._ARCHIVES.append(archive)
        # Set variables:
        self._IS_LOADED = True
        self._LAST_FETCHED: datetime = datetime.utcnow().replace(tzinfo=timezone.utc)
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
