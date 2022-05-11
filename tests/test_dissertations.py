"""
test_dissertations.py

Tests everything in the classes.dissertations module
"""

# Imports
import re
from collections.abc import Generator
from datetime import date
from decouple import config
import pandas as pd
import pytest
from sickle import Sickle
from sickle.models import Record
from classes.dissertations import (
    DISSERTATION_NO_URL_MSG,
    DISSERTATIONS_FILE_SERVER_BASE,
    MANDATORY_HEADER_KEYS,
    MANDATORY_METADATA_KEYS,
    UUID_PATTERN,
    record_to_dict,
    Dissertation,
    DissertationList,
    RecordObjectException
)

# Constants
REPOSITORY_URL = config('REPOSITORY_URL')


# Helper functions
def get_test_record() -> Record:
    """
    This function fetches an OAI Record from the repository and returns
    is for usage in the test suite.
    :return:    A sickle.models.Record object
    """
    oai_url = REPOSITORY_URL
    sickle = Sickle(oai_url)
    records = sickle.ListRecords(metadataPrefix='oai_dc',
                                 set=config('OAI_SET'))
    return records.next()


# Test suite
class TestDissertation:
    """
    Test suite for the dissertations module.
    """

    def test_exception_record_to_dict(self):
        with pytest.raises(RecordObjectException):
            record_to_dict('not a record')

    def test_pass_record_to_dict(self):
        record = get_test_record()
        record_dict = record_to_dict(record)
        assert isinstance(record_dict, dict)
        assert (
            'header' in record_dict.keys() and
            'metadata' in record_dict.keys()
        )
        for key in MANDATORY_HEADER_KEYS:
            assert key in record_dict['header'].keys()
        for key in MANDATORY_METADATA_KEYS:
            assert key in record_dict['metadata'].keys()
            assert isinstance(record_dict['metadata'][key], list)

    def test_fail_create_from_record(self):
        with pytest.raises(RecordObjectException):
            Dissertation.create_from_record('not a record')

    def test_pass_create_from_record(self):
        record = get_test_record()
        assert isinstance(Dissertation.create_from_record(record), Dissertation)

    def test_properties_except_date(self):
        record = get_test_record()
        record_dict = record_to_dict(record)
        dissertation = Dissertation.create_from_record(record)
        assert isinstance(dissertation.id_dissertation, str)
        assert re.match(UUID_PATTERN, dissertation.id_dissertation) is not None
        with pytest.raises(TypeError):
            dissertation.id_dissertation = 42
        assert isinstance(dissertation.title, str)
        assert dissertation.title == '|'.join(record_dict['metadata']['title'])
        assert (
            dissertation.authors == ', '.join(dissertation.authors_list) and
            dissertation.publishers == ', '.join(dissertation.publishers_list)
            and dissertation.contributors == ', '.join(dissertation.contributors_list)
        )
        assert (dissertation.url.startswith(DISSERTATIONS_FILE_SERVER_BASE))
        dissert_dict = Dissertation(
            '', [], [], [], [], [], ['https://www.example.com'], False
        )
        assert dissert_dict.url == DISSERTATION_NO_URL_MSG

    def test_date_property(self):
        record = get_test_record()
        record_dict = record_to_dict(record)
        dissertation = Dissertation.create_from_record(record)
        assert isinstance(dissertation.date, date)
        record_dict['metadata']['date'] = ['2022']
        dissert_dict = Dissertation(
            record_dict['header']['identifier'], [], [], [], [],
            record_dict['metadata']['date'], [], False
        )
        assert dissert_dict.date == date(2022, 6, 1)
        record_dict['metadata']['date'] = ['a022']
        dissert_dict = Dissertation(
            record_dict['header']['identifier'], [], [], [], [],
            record_dict['metadata']['date'], [], False
        )
        assert dissert_dict.date == date(2038, 1, 20)

    def test_str(self):
        record = get_test_record()
        record_dict = record_to_dict(record)
        dissertation = Dissertation.create_from_record(record)
        string_version = "{authors}. {title} ({date})".format(
            authors=', '.join(record_dict['metadata']['creator']),
            title='|'.join(record_dict['metadata']['title']),
            date=record_dict['metadata']['date'][0].split('-')[0]
        )
        assert str(dissertation) == string_version

    def test_repr(self):
        record = get_test_record()
        dissertation = Dissertation.create_from_record(record)
        repr_version = f"<Dissertation {dissertation.id_dissertation}>"
        assert repr(dissertation) == repr_version


class TestDissertationList:
    """
    Test suite for the DissertationList object.
    """

    def test_init(self):
        d_list = DissertationList()
        assert isinstance(d_list, DissertationList)
        assert isinstance(d_list.data, pd.DataFrame)
        columns = ['title', 'publication_date', 'url', 'deleted']
        assert list(columns) == list(d_list.data.columns)

    def test_append_exception(self):
        d_list = DissertationList()
        with pytest.raises(TypeError):
            d_list.append('not a dissertation')

    def test_append(self):
        record = get_test_record()
        dissertation = Dissertation.create_from_record(record)
        d_list = DissertationList()
        d_list.append(dissertation)
        assert d_list.data.shape == (1, 4)
        # Trying to append the same dissertation twice should fail
        with pytest.warns(UserWarning):
            d_list.append(dissertation)
        assert d_list.data.shape == (1, 4)

    def test_dunders(self):
        record = get_test_record()
        dissertation = Dissertation.create_from_record(record)
        d_list = DissertationList()
        assert str(d_list).startswith('Empty DataFrame')
        assert repr(d_list).startswith('Empty DataFrame')
        assert len(d_list) == 0
        d_list.append(dissertation)
        assert str(d_list).endswith('[1 rows x 4 columns]')
        assert repr(d_list).endswith('[1 rows x 4 columns]')
        assert len(d_list) == 1
        iterator = d_list.__iter__()
        assert isinstance(iterator, Generator)
        item = next(iterator)
        assert isinstance(item, tuple)
        assert isinstance(item[1], pd.Series)

    def test_data_setter(self):
        record = get_test_record()
        dissertation = Dissertation.create_from_record(record)
        d_list = DissertationList()
        d_list.append(dissertation)
        df = d_list.data.copy()
        bad_df = df[['title', 'publication_date']].copy()
        with pytest.raises(KeyError):
            d_list.data = bad_df
        with pytest.raises(TypeError):
            d_list.data = 'this is not a valid DataFrame'
        random_date = date(2038, 1, 20)
        df['publication_date'] = random_date
        d_list.data = df
        index = d_list.data.index[0]
        assert d_list.data.at[index, 'publication_date'] == random_date

    def test_add_column(self):
        record = get_test_record()
        dissertation = Dissertation.create_from_record(record)
        d_list = DissertationList()
        d_list.append(dissertation)
        with pytest.raises(TypeError):
            d_list.add_column(42)
        with pytest.raises(ValueError):
            d_list.add_column('title')
        d_list.add_column('new_column', 42)
        assert 'new_column' in d_list.data.columns
        index = d_list.data.index[0]
        assert d_list.data.at[index, 'new_column'] == 42
