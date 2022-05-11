"""
dissertations.py

Module for dissertations' data fetched from the OAI repository
"""

# Imports
import re
import warnings
from datetime import date
from decouple import config
import numpy as np
import pandas as pd
from sickle.models import Record

# Constants
DISSERTATION_NO_URL_MSG = 'URL not found'
DISSERTATIONS_FILE_SERVER_BASE = config('DISSERTATIONS_SERVER')
MANDATORY_HEADER_KEYS = [
    'identifier',
    'deleted'
]
MANDATORY_METADATA_KEYS = [
    'title',
    'creator',
    'publisher',
    'contributor',
    'date',
    'identifier'
]
NULL_UUID = '00000000-0000-0000-0000-000000000000'
UUID_PATTERN = r'[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$'


# Functions
def record_to_dict(oai_record: Record) -> dict:
    """
    This function take a sickle.models.Record and converts it into a dictionary
    containing the record's metadata and filler values where mandatory data
    is not provided.

    :param oai_record:      The record request from the repository.
    :type oai_record:       sickle.models.Record
    :return:                The metadata dictionary.
    """
    if not isinstance(oai_record, Record):
        raise RecordObjectException('oai_record')

    record = {
        'header': {
            'identifier': NULL_UUID,
            'deleted': False
        },
        'metadata': {
            'title': [],
            'creator': [],
            'publisher': [],
            'contributor': [],
            'date': [],
            'identifier': []
        }
    }

    for key in MANDATORY_HEADER_KEYS:
        if hasattr(oai_record.header, key):
            record['header'][key] = getattr(oai_record.header, key)

    for key in MANDATORY_METADATA_KEYS:
        if key in oai_record.metadata:
            record['metadata'][key] = oai_record.metadata[key]

    return record


# Classes
class RecordObjectException(Exception):
    """
    The user passes an argument to a method that is not a
    sickle.models.Record object.
    """
    def __init__(self, argument: str):
        """
        Exception constructor.

        :param argument:    Name of the argument that isn't the right object.
        :type argument:     str
        """
        self.message = f"{argument} must be a valid sickle.models.Record."
        super(RecordObjectException, self).__init__(self.message)


class Dissertation:
    """
    Dissertation class

    This class contains all relevant metadata fetched from the OAI repository
    for dissertations and theses.

    Since it gets its metadata from a sickle.models.Record object, all
    metadata is enclosed in lists even if there is only one list item.

    Class properties are used throughout the class to return every metadata
    in the right format.
    """
    def __init__(self,
                 db_identifier: str,
                 title: list,
                 creators: list,
                 publishers: list,
                 contributors: list,
                 publication_date: list,
                 identifiers: list,
                 is_deleted: bool = False):
        """
        Class constructor

        Dissertation object instantiation should always be done through
        the create_from_record() class method.

        :param db_identifier:       The database UUID identifier.
        :type db_identifier:        str
        :param title:               The dc.title field's content.
        :type title:                list
        :param creators:            The dc.creator field's content.
        :type creators:             list
        :param publishers:          The dc.publisher field's content.
        :type publishers:           list
        :param contributors:        The dc.contributor field's content.
        :type contributors:         list
        :param publication_date:    The dc.date field's content.
        :type publication_date:     list
        :param identifiers:         The dc.identifier field's content.
        :type identifiers:          list
        :param is_deleted:          Indicates record is deleted in repository.
        :type is_deleted:           bool
        """
        self.id_dissertation = db_identifier
        self.__title = title
        self.__authors = creators
        self.__publishers = publishers
        self.__contributors = contributors
        self.__dates = publication_date
        self.__url = identifiers
        self.is_deleted = is_deleted

    @classmethod
    def create_from_record(cls, oai_record: Record):
        """
        This method retrieves data from a sickle.models.Record's header and
        metadata attributes, instantiates and returns a Dissertation object.

        :param oai_record:          A record fetched from the OAI repository.
        :type oai_record:           sickle.models.Record
        :return:                    A Dissertation object.
        """
        if not isinstance(oai_record, Record):
            raise RecordObjectException('oai_record')

        record = record_to_dict(oai_record)

        return cls(
            record['header']['identifier'],
            record['metadata']['title'],
            record['metadata']['creator'],
            record['metadata']['publisher'],
            record['metadata']['contributor'],
            record['metadata']['date'],
            record['metadata']['identifier'],
            record['header']['deleted']
        )

    @property
    def id_dissertation(self) -> str:
        """
        Returns the dissertation's repository UUID.
        """
        return self.__id_dissertation

    @id_dissertation.setter
    def id_dissertation(self, db_identifier):
        """
        Strips the UUID part of the dissertation's repository identifier
        from the repo's identifier prefix.
        :param db_identifier:  The repository identifier with its prefix.
        :type db_identifier:   str
        """
        if db_identifier and not isinstance(db_identifier, str):
            raise TypeError("identifier must be a valid string.")

        matching_id = re.search(UUID_PATTERN, db_identifier)
        if matching_id:
            self.__id_dissertation = matching_id.group(0)

    @property
    def title(self) -> str:
        """
        Returns the title in a single string.
        """
        return '|'.join(self.__title)

    @property
    def authors(self) -> str:
        """
        Returns the authors' list in a single string.
        """
        return ', '.join(self.__authors)

    @property
    def authors_list(self) -> list:
        """
        Returns the authors' list as is.
        """
        return self.__authors

    @property
    def publishers(self) -> str:
        """
        Returns the publisher's list in a single string.
        """
        return ', '.join(self.__publishers)

    @property
    def publishers_list(self) -> list:
        """
        Returns the publishers' list as is.
        """
        return self.__publishers

    @property
    def contributors(self) -> str:
        """
        Returns the contributors' list in a single string.
        """
        return ', '.join(self.__contributors)

    @property
    def contributors_list(self) -> list:
        """
        Returns the contributors' list as is.
        :return:
        """
        return self.__contributors

    @property
    def date(self) -> date:
        """
        Returns a single valid ISO format date.
        """
        date_pattern = r'\d{4}-\d{2}-\d{2}$'
        year_pattern = r'\d{4}$'
        iso_dates = [
            full_date for full_date in self.__dates if re.match(date_pattern,
                                                                full_date,
                                                                re.ASCII)
        ]
        years_only = [
            one_year for one_year in self.__dates if re.match(year_pattern,
                                                              one_year,
                                                              re.ASCII)
        ]
        if iso_dates:
            return date.fromisoformat(iso_dates[0])
        if years_only:
            return date.fromisoformat(f"{years_only[0]}-06-01")

        # For the idiots that can't catalog a valid date...
        return date.fromisoformat('2038-01-20')

    @property
    def url(self) -> str:
        """
        Returns a single URL pointing to the dissertation's .pdf file.
        """
        urls = [
            url for url in self.__url if url.startswith(DISSERTATIONS_FILE_SERVER_BASE)
        ]
        if urls:
            return urls[0]
        return DISSERTATION_NO_URL_MSG

    def __str__(self):
        return f"{self.authors}. {self.title} ({self.date.year})"

    def __repr__(self):
        return f"<Dissertation {self.id_dissertation}>"


class DissertationList:
    """
    DissertationList class

    This class is built upon the shoulders of a giant : a Pandas DataFrame. Its
    primary use is to gather data from Dissertation objects and store it inside
    an object that will be reused for reporting.
    """
    def __init__(self):
        """
        Class constructor

        The instantiation only provides the user with an empty DataFrame. Only
        the structure is predetermined. The data is then added using the class'
        append method.
        """
        empty_dict = {
            'title': [],
            'publication_date': [],
            'url': [],
            'deleted': []
        }
        self.__data = pd.DataFrame(empty_dict)

    @property
    def data(self) -> pd.DataFrame:
        """
        Returns the DataFrame
        """
        return self.__data

    @data.setter
    def data(self, other_data: pd.DataFrame):
        """
        This setter method is used primarily to ease the manipulation of the
        DataFrame object that is the data attribute.
        :param other_data:      The incoming DataFrame
        :type other_data:       pd.DataFrame
        """
        if not isinstance(other_data, pd.DataFrame):
            raise TypeError("data attribute must be set with a DataFrame.")

        self_columns = list(self.__data.columns)
        other_columns = list(other_data.columns)

        if self_columns != other_columns:
            raise KeyError(
                "DataFrame object must match the existing data attribute."
            )

        self.__data = other_data

    def add_column(self, label: str, default_value=np.nan):
        """
        Adds a column to the data property's DataFrame
        :param label:           The new column's label.
        :type label:            str
        :param default_value:   A default value for all rows.
        """
        if not isinstance(label, str):
            raise TypeError("Label must be a valid string.")

        if label in self.__data.columns:
            raise ValueError(f"Column {label} already exists.")

        self.__data[label] = default_value

    def append(self, dissertation: Dissertation):
        """
        Adds a Dissertation object to the class' data property
        :param dissertation:    The dissertation that will be added to the list.
        :type dissertation:     Dissertation
        """
        if not isinstance(dissertation, Dissertation):
            raise TypeError("Object provided must be a valid Dissertation.")

        if dissertation.id_dissertation in self.__data.index.array:
            warnings.warn(
                f"Duplicate found: {repr(dissertation)} not added to list."
            )
        else:
            metadata = {
                'title': [dissertation.title],
                'publication_date': [dissertation.date],
                'url': [dissertation.url],
                'deleted': [dissertation.is_deleted]
            }

            df = pd.DataFrame(metadata, index=[dissertation.id_dissertation])
            self.__data = pd.concat([self.__data, df])

    def __str__(self) -> str:
        """
        Returns the string version of the data property
        """
        return str(self.data)

    def __repr__(self) -> str:
        """
        Returns the repr version of the data property
        """
        return repr(self.data)

    def __len__(self) -> int:
        """
        Returns the number of rows inside the list.
        """
        shape = self.data.shape
        return shape[0]

    def __iter__(self):
        """
        Returns the DataFrame.iterrows generator.
        """
        return self.__data.iterrows()
