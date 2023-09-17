#!/usr/bin/env python3
"""
    File: Archive.py
"""
from typing import Optional, Callable, Any
import os
import requests
from datetime import datetime
import pytz
try:
    from common import __type_error__, convert_to_utc, __raise_for_http_error__
    import common
    from Exceptions import ArchiveError, RequestReadTimeout, ParameterError
except ImportError:
    from PyPapertrail.common import __type_error__, convert_to_utc, __raise_for_http_error__
    import PyPapertrail.common as common
    from PyPapertrail.Exceptions import ArchiveError, RequestReadTimeout, ParameterError

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
            Self = TypeVar("Self", bound="Archive")
        except ImportError:
            print("FATAL: Unable to define Self.")
            exit(129)


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
                 last_fetched: Optional[datetime] = None,
                 ) -> None:
        """
        Initialize the archive.
        :param api_key: Str: The api key.
        :param raw_archive: Optional[dict]: The raw dict from papertrail listing. Default = None
            Note: if raw_archive is used, last_fetched must be defined.
        :param from_dict: Optional[dict]: Load from a saved dict created by __to_dict__().
        :return: None
        """
        # Type checks:
        if not isinstance(api_key, str):
            __type_error__("api_key", "str", api_key)
        elif raw_archive is not None and not isinstance(raw_archive, dict):
            __type_error__("raw_archive", "dict", raw_archive)
        elif from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        elif last_fetched is not None and not isinstance(last_fetched, datetime):
            __type_error__("last_fetched", "datetime", last_fetched)
        # Parameter checks:
        if (raw_archive is None and from_dict is None) or (raw_archive is not None and from_dict is not None):
            error: str = "ParameterError: Either from_dict or raw_archive must be defined, but not both."
            raise ParameterError(error)
        elif raw_archive is not None and last_fetched is None:
            error: str = "ParameterError: If using raw_archive, last_fetched must be defined."
            raise ParameterError(error)

        # Store api key, and last fetched:
        self._api_key: str = api_key
        self._last_fetched: Optional[datetime] = None
        if last_fetched is not None:
            self._last_fetched = convert_to_utc(last_fetched)
        # Define properties:
        self._start_time: datetime = convert_to_utc(datetime(year=1970, month=1, day=1))
        self._end_time: datetime = convert_to_utc(datetime(year=1970, month=1, day=1))
        self._formatted_start_time: str = ''
        self._formatted_duration: str = ''
        self._file_name: str = ''
        self._file_size: int = -1
        self._link: str = ''
        self._duration: int = -1
        self._is_downloaded: bool = False
        self._download_path: Optional[str] = None
        self._downloading: bool = False
        # Load archive properties:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif raw_archive is not None:
            self.__from_raw_archive__(raw_archive)
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
            self._start_time = convert_to_utc(datetime.fromisoformat(raw_archive['start'][:-1]))
            self._end_time = convert_to_utc(datetime.fromisoformat(raw_archive['end'][:-1]))
            self._formatted_start_time = raw_archive['start_formatted']
            self._formatted_duration = raw_archive['duration_formatted']
            self._file_name = raw_archive['filename']
            self._file_size = int(raw_archive['filesize'])
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
        except (KeyError, ValueError) as e:
            error: str = ("KeyError or ValueError while extracting data from raw_archive. Maybe papertrail changed "
                          "their response.")
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
            self._start_time = datetime.fromisoformat(from_dict['start_time'])
            self._end_time = datetime.fromisoformat(from_dict['end_time'])
            self._formatted_start_time = from_dict['formatted_start_time']
            self._formatted_duration = from_dict['formatted_duration']
            self._file_name = from_dict['file_name']
            self._file_size = from_dict['file_size']
            self._link = from_dict['link']
            self._duration = from_dict['duration']
            self._is_downloaded = from_dict['is_downloaded']
            self._download_path = from_dict['download_path']
        except (KeyError, ValueError) as e:
            error: str = "Invalid dict passed to __from_dict__()"
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
                 argument: Any = None,
                 chunk_size: int = 8196,
                 ) -> tuple[bool, str | int, Optional[str]]:
        """
        Download this archive.
        :param destination_dir: Str. Directory to save file in.
        :param file_name: Optional[str]. Override the default file name with this file name. Default=None
        :param overwrite: Bool. Overwrite existing files. Default = False
        :param callback: Optional[Callable]. The call back to call each chunk downloaded. Default = None.
            The function signature is: callback (archive: Archive, bytes_downloaded: int, argument: Optional[Any]) -> None
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
            error: str = "requests.RequestException: err_num=%i, strerror='%s'" % (e.errno, e.strerror)
            raise ArchiveError(error, exception=e)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            file_handle.close()
            self._downloading = False
            __raise_for_http_error__(request=r, exception=e)
        # Call the callback with zero bytes downloaded:
        if callback is not None:
            try:
                callback(self, 0, argument)
            except SystemExit as e:
                raise e
            except Exception as e:
                self._downloading = False
                error: str = "Exception during callback execution."
                raise ArchiveError(error, exception=e)
        # Download started:
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
# Overrides:
##################################
    def __eq__(self, other: Self | int | str) -> bool:
        """
        Equality test, tests start time equality if other == System object, file size if other == Int, and
            file name if other == Str.
        :param other: System | int | str: The other object.
        :return: Bool.
        """
        if isinstance(other, type(self)):
            return self._start_time == other._start_time
        elif isinstance(other, int):
            return self._file_size == other
        elif isinstance(other, str):
            return self._file_name == other
        error: str = "Cannot compare Archive to %s" % str(type(other))
        raise TypeError(error)

    def __str__(self) -> str:
        """
        Refer to this as a str, produce the file name.
        :return: Str: The file name.
        """
        return self._file_name

    def __int__(self) -> int:
        """
        Refer to this as an int, produce the file size in bytes.
        :return: Int: The file size in bytes.
        """
        return self._file_size

    def __gt__(self, other: Self | datetime) -> bool:
        """
        Compare if this is greater than 'other', which is either an Archive object or a datetime object.
        :param other: Archive | datetime: other can be either an Archive object that compares start_times, or a
            datetime which is converted to UTC then compared to start_time.
        :return: Bool
        """
        if isinstance(other, type(self)):
            return self._start_time > other.start_time
        elif isinstance(other, datetime):
            compare_time: datetime = convert_to_utc(other)
            return self._start_time > compare_time
        error: str = "Can only compare to other Archive objects or datetime objects."
        raise TypeError(error)

    def __lt__(self, other: Self | datetime) -> bool:
        """
        Compare if this is less than 'other', which is either an Archive or a datetime object.
        :param other: Archive | datetime: other can be either an Archive object that compares start_times, or a
            datetime object which is converted to UTC then compared to start_time.
        :return: Bool
        """
        if isinstance(other, type(self)):
            return self._start_time < other.start_time
        elif isinstance(other, datetime):
            compare_time: datetime = convert_to_utc(other)
            return self._start_time < compare_time
        error: str = "Can only compare to other Archive objects or datetime objects."
        raise TypeError(error)

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

    @property
    def last_fetched(self) -> datetime:
        """
        Last time this was read from the server, times in UTC.
        :return: Datetime object.
        """
        return self._last_fetched
