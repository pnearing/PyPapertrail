#!/usr/bin/env python3

from typing import Optional, Callable, Iterator
import os
import requests
from datetime import datetime, timezone
from common import BASE_URL, is_timezone_aware
from Exceptions import ArchiveError


class Archive(object):
    """
    Class representing a Papertrail archive.
    """
    def __init__(self, raw_archive: dict, api_key: str) -> None:
        """
        Initialize the archive.
        :param raw_archive: Dict. The raw dict from papertrail listing.
        :param api_key: Str. The api key.
        :return: None
        """
        # Store api key:
        self._api_key: str = api_key
        # Extract data from raw_archive dict:
        try:
            self._start_time: datetime = datetime.fromisoformat(raw_archive['start'][:-1]).replace(tzinfo=timezone.utc)
            self._end_time: datetime = datetime.fromisoformat(raw_archive['end'][:-1]).replace(tzinfo=timezone.utc)
            self._formatted_start_time: str = raw_archive['start_formatted']
            self._formatted_duration: str = raw_archive['duration_formatted']
            self._file_name: str = raw_archive['filename']
            self._file_size: int = raw_archive['filesize']
            self._link: str = raw_archive['_links']['download']['href']
        except KeyError:
            error: str = "KeyError while extracting data from raw_archive. Maybe papertrail changed their response."
            raise ArchiveError(error)
        # Calculate duration in minutes:
        self._duration: int
        if self._formatted_duration.lower() == '1 hour':
            self._duration = 60  # 1 hour in minutes
        elif self._formatted_duration.lower() == '1 day':
            self._duration = 24 * 60  # 1 day in minutes.
        else:
            raise NotImplementedError("Unknown duration_formatted value.")
        # Store downloading properties:
        self._downloading: bool = False
        self._is_downloaded: bool = False
        self._download_path: Optional[str] = None
        return

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

    def download(self,
                 destination_dir: str,
                 file_name: Optional[str] = None,
                 overwrite: bool = False,
                 callback: Optional[Callable] = None,
                 argument: Optional[object] = None,
                 chunk_size: int = 8196,
                 raise_on_error: bool = True,
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
        :param raise_on_error: Bool, Raise ArchiveError instead of returning False when an error occurs. Default = True.
        :return: Tuple[bool, str | int, Optional[str]]: The first element is a status flag indicating success, True
                    being a success, and False a failure. If the first element is True, then the second element will be
                    the total number of bytes downloaded, and the third element will be the path to the downloaded file.
                    If the first element is False, the second element will be an error message indicating what went
                    wrong, and the third element will optionally be the path to the partially downloaded file.
        """
        # Check to see if we're already downloading:
        if self._downloading:
            error: str = "Already downloading."
            if raise_on_error:
                raise ArchiveError(error)
            else:
                return False, error, None
        else:
            self._downloading = True
        # Validate destination:
        if not os.path.isdir(destination_dir):
            self._downloading = False
            error: str = "Destination: %s, is not a directory" % destination_dir
            if raise_on_error:
                raise ArchiveError(error, destination_dir=destination_dir)
            else:
                return False, error, None
        # Get the filename, and build the full download path.:
        if file_name is None:
            file_name = self._file_name
        download_path: str = os.path.join(destination_dir, file_name)
        # Check if the download path exists:
        if not overwrite and os.path.exists(download_path):
            self._downloading = False
            error: str = "Destination: %s, already exists." % download_path
            if raise_on_error:
                raise ArchiveError(error, download_path=download_path)
            else:
                return False, error, download_path
        # Open the file:
        try:
            file_handle = open(download_path, 'wb')
        except IOError as e:
            self._downloading = False
            error: str = "Failed to open '%s' for writing: %s" % (download_path, e.strerror)
            if raise_on_error:
                raise ArchiveError(error, exception=e, download_path=download_path)
            else:
                return False, error, download_path
        # Make the http request:
        try:
            headers = {"X-Papertrail-Token": self._api_key}
            r = requests.get(self._link, headers=headers, stream=True)
            r.raise_for_status()
        except requests.HTTPError as e:
            file_handle.close()
            self._downloading = False
            error: str = "HTTP request failed. ErrNo: %i ErrMsg: %s." % (e.errno, e.strerror)
            if raise_on_error:
                raise ArchiveError(error, exception=e, download_path=download_path, )
            else:
                return False, error, download_path
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
                    if raise_on_error:
                        raise ArchiveError(error, exception=e)
                    else:
                        return False, error, file_name
        # Download complete:
        file_handle.close()
        # Sanity checks for the download:
        if download_size != written_size:
            self._downloading = False
            error: str = "Downloaded bytes does not match written bytes. DL:%i != WR:%i" % (download_size, written_size)
            if raise_on_error:
                raise ArchiveError(
                    error,
                    download_path=download_path,
                    downloaded_bytes=download_size,
                    written_bytes=written_size
                )
            else:
                return False, error, download_path
        self._downloading = False
        self._is_downloaded = True
        self._download_path = download_path
        return True, download_size, download_path


class Archives(object):
    """Class to hold papertrail archive calls."""
    _ARCHIVES: list[Archive] = []

    def __init__(self, api_key: str, do_load=True) -> None:
        """
        Initialize Papertrail API.
        :param api_key: Str, the papertrail "API Token" found in papertrail under: settings / profile / API Token
        :param do_load: Bool, Load the archive list on initialization. Default = True.
        :raises: ArchiveError: Raises ArchiveError on error during loading.
        :returns: None
        """
        self._api_key = api_key
        self._last_fetched: Optional[datetime] = None
        self._is_loaded: bool = False
        if do_load:
            self.load()
        return

    @property
    def last_fetched(self) -> Optional[datetime]:
        return self._last_fetched

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def load(self, raise_on_error: bool = True) -> tuple[bool, str]:
        """
        Load the archive list from server.
        :param raise_on_error: Bool, Raise an error instead of returning False on error.
        :return: Tuple[bool, str]: First element, the bool, is True if successful, and False if not, if the first
                    element is True, the second element, the str is the message: "OK"; And if the first element is
                    False, the second element will be an error message.
        """
        # Generate list url and headers:
        list_url = BASE_URL + 'archives.json'
        headers = {"X-Papertrail-Token": self._api_key}
        # Request the response:
        r: requests.Response = requests.get(list_url, headers=headers)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            error: str = "Request HTTP error #%i:%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise ArchiveError(error, exception=e, request=r)
            else:
                return False, error
        except requests.RequestException as e:
            error: str = "Requests Exception: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise ArchiveError(error, exception=e, request=r)
            else:
                return False, error
        except requests.ReadTimeout as e:
            error: str = "Read Timeout: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise ArchiveError(error, exception=e, request=r)
        # Parse the response:
        try:
            response = r.json()
        except requests.JSONDecodeError as e:
            error: str = "Server sent invalid json: error_num=%i, strerror=%s" % (e.errno, e.strerror)
            if raise_on_error:
                raise ArchiveError(error, exception=e, request=r)
            else:
                return False, error
        # Return the list as list of Archive objects:
        self._ARCHIVES = []
        for raw_archive in response:
            archive = Archive(raw_archive, api_key=self._api_key)
            self._ARCHIVES.append(archive)
        self._is_loaded = True
        self._last_fetched: datetime = datetime.utcnow().replace(tzinfo=timezone.utc)
        return True, "OK"

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


