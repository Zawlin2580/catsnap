from __future__ import unicode_literals

from mock import patch, Mock, MagicMock
from nose.tools import eq_
from boto.dynamodb.exceptions import DynamoDBKeyNotFoundError

from catsnap.document.tag import Tag

class TestTag():
    @patch('catsnap.document.Config')
    def test_get_table_creates_table_conection(self, Config):
        config = Mock()
        Config.return_value = config
        mock_table = Mock()
        config.table.return_value = mock_table

        tag = Tag('cats')
        table = tag._table()
        eq_(tag._stored_table, mock_table)
        eq_(table, mock_table)
        config.table.assert_called_with('tag')

    @patch('catsnap.document.Config')
    def test_get_table_is_memoized(self, Config):
        config = Mock()
        Config.return_value = config
        tag = Tag('dogs')
        mock_table = Mock()
        tag._stored_table = mock_table

        table = tag._table()
        eq_(table, mock_table)
        eq_(config.table.call_count, 0)

class TestAddingFile():
    def test_sends_to_dynamo(self):
        item = Mock()
        table = Mock()
        table.get_item.side_effect = DynamoDBKeyNotFoundError('no such tag')
        table.new_item.return_value = item
        tag = Tag('cat')
        tag._stored_table = table

        tag.add_file('Sewing_cat.gif')
        table.new_item.assert_called_with(hash_key='cat',
                attrs={ 'Sewing_cat.gif': 'Sewing_cat.gif'})
        item.put.assert_called_with()

    def test_updates_existing_tag(self):
        table = Mock()
        item = MagicMock()
        table.get_item.return_value = item

        tag = Tag('dog')
        tag._stored_table = table
        tag.add_file('dancing_dog.gif')

        eq_(table.new_item.call_count, 0, "shouldn't've made a new entry")
        item.put.assert_called_with()
        item.__setitem__.assert_called_with('dancing_dog.gif', 'dancing_dog.gif')

class TestGetFilenames():
    def test_get_filenames(self):
        item = MagicMock()
        item.keys.return_value = ['tag', 'BADCAFE', 'DEADBEEF']
        table = Mock()
        table.get_item.return_value = item
        tag = Tag('cat')
        tag._stored_table = table

        filenames = tag.get_filenames()
        eq_(filenames, ['BADCAFE', 'DEADBEEF'])
        table.get_item.assert_called_with('cat')

    def test_returns_empty_list_if_no_such_tag_exists(self):
        tag = Tag('cat')
        table = Mock()
        table.get_item.side_effect = DynamoDBKeyNotFoundError('no such tag')
        tag._stored_table = table

        eq_(tag.get_filenames(), [])
