import json
import nose
import mock
from mock import patch
from restpy import formats


@patch.object(formats, '_formatter_registry')
def test_formatter_registry(registry_mock):
    A = formats.FormatterRegistry(
        'A', (formats.BaseFormatter,), {'name': 'a'}
    )
    registry_mock.__setitem__.assert_called_with('a', A)


def test_base_formatter_serialize_should_be_abstract():
    nose.tools.assert_raises(
        NotImplementedError,
        formats.BaseFormatter.serialize,
        {}
    )


def test_base_formatter_unserialize_should_be_abstract():
    nose.tools.assert_raises(
        NotImplementedError,
        formats.BaseFormatter.unserialize,
        ''
    )


test_data = {
    'test': 1,
    'test2': {
        'sub1': 1,
        'sub2': 2,
        'sub3': {
            'subb4': 3,
            'subb5': [{'a': 1}, {'b': 2}]
        }
    }
}


def test_json_format_params():
    assert formats.JsonFormat.name == 'json'
    assert formats.JsonFormat.content_type == 'application/json'


def test_json_format_unserialize():
    assert formats.JsonFormat.unserialize(json.dumps(test_data)) == test_data


@patch.object(json, 'loads')
def test_json_format_unserialize_value_error(loads_mock):
    loads_mock.side_effect = ValueError('Wrong data')
    nose.tools.assert_raises(
        formats.LoadError,
        formats.JsonFormat.unserialize,
        ''
    )


@patch.object(json, 'dumps')
def test_json_format_serialize_value_error(dumps_mock):
    dumps_mock.side_effect = ValueError('Wrong type object passed')
    nose.tools.assert_raises(
        formats.LoadError,
        formats.JsonFormat.serialize,
        {}
    )


def test_get_formatter():
    cls = mock.Mock(spec=formats.BaseFormatter)
    with patch.dict(formats._formatter_registry, {'a': cls}, clear=True):
        assert formats.get_formatter('a') == cls


def test_get_formatter_unexisting():
    with patch.dict(formats._formatter_registry, {}, clear=True):
        assert formats.get_formatter('a') is None