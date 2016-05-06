import json
import mock
import pytest

from mock import patch

from restea import errors
from restea import formats
from restea import fields
from restea.resource import Resource


def create_resource_helper(
    method='GET',
    headers={},
    data=None,
    formatter=None
):
    request = mock.Mock(method=method, headers=headers, data=data)
    original_request = mock.Mock()
    request._original_request = original_request

    if not formatter:
        formatter = mock.Mock()

    return Resource(request, formatter), request, formatter, original_request


def test_init():
    resource, req_mock, formatter_mock, original_req= create_resource_helper()
    assert resource.request == original_req
    assert resource.formatter == formatter_mock
    assert isinstance(resource.fields, fields.FieldSet)


def test_get_method_name_list():
    resource, _, _, _ = create_resource_helper()
    assert 'list' == resource._get_method_name(has_iden=False)


def test_get_method_name_show():
    resource, _, _, _ = create_resource_helper()
    assert 'show' == resource._get_method_name(has_iden=True)


def test_get_method_name_edit():
    resource, _, _, _ = create_resource_helper(method='PUT')
    assert 'edit' == resource._get_method_name(has_iden=True)


def test_get_method_name_edit_without_iden():
    resource, _, _, _ = create_resource_helper(method='PUT')

    with pytest.raises(errors.BadRequestError) as e:
        resource._get_method_name(has_iden=False)
    assert 'Given method requires iden' in str(e)


def test_get_method_name_create():
    resource, _, _, _ = create_resource_helper(method='POST')
    assert 'create' == resource._get_method_name(has_iden=False)


def test_get_method_name_create_with_id():
    resource, _, _, _ = create_resource_helper(method='POST')

    with pytest.raises(errors.BadRequestError) as e:
        resource._get_method_name(has_iden=True)
    assert "Given method shouldn't have iden" in str(e)


def test_get_method_name_delete():
    resource, _, _, _ = create_resource_helper(method='DELETE')
    assert 'delete' == resource._get_method_name(has_iden=True)


def test_get_method_name_unpecefied_method():
    resource, _, _, _ = create_resource_helper(method='HEAD')

    with pytest.raises(errors.MethodNotAllowedError) as e:
        resource._get_method_name(has_iden=True)
    assert 'Method "HEAD" is not supported' in str(e)


def test_get_method_name_method_override():
    headers = {'HTTP_X_HTTP_METHOD_OVERRIDE': 'PUT'}
    resource, _, _, _ = create_resource_helper(method='HEAD', headers=headers)
    assert 'edit' == resource._get_method_name(has_iden=True)


def test_iden_required_positive():
    resource, _, _, _ = create_resource_helper()
    assert resource._iden_required('show')
    assert resource._iden_required('edit')
    assert resource._iden_required('delete')


def test_iden_required_negative():
    resource, _, _, _ = create_resource_helper()
    assert resource._iden_required('create') is False
    assert resource._iden_required('list') is False


def test_match_responce_to_fields():
    resource, _, _, _ = create_resource_helper()
    resource.fields = mock.Mock(spec=fields.FieldSet)
    resource.fields.field_names = ['name1', 'name2', 'name3']

    data = {'name1': 1, 'name2': 2, 'name3': 3, 'name4': 4}
    expected_data = {'name1': 1, 'name2': 2, 'name3': 3}

    assert resource._match_responce_to_fields(data) == expected_data


def test_match_responce_list_to_fields():
    resource, _, _, _ = create_resource_helper()
    resource.fields = mock.Mock(spec=fields.FieldSet)
    resource.fields.field_names = ['name1', 'name2', 'name3']

    lst = [
        {'name1': 1, 'name2': 2, 'name3': 3, 'name4': 4},
        {'name1': 5, 'name2': 6},
    ]
    expected_lst = [
        {'name1': 1, 'name2': 2, 'name3': 3},
        {'name1': 5, 'name2': 6},
    ]

    assert list(resource._match_resource_list_to_fields(lst)) == expected_lst


def test_apply_decorators():
    resource, _, _, _ = create_resource_helper()
    resource.create = mock.MagicMock(return_value={
        'test1': 0,
        'test2': 0
    })

    def dummy_decorator1(func):
        def wrapper(*a, **kw):
            res = func(*a, **kw)
            res['test1'] = 'replacement #1'
            return res
        return wrapper

    def dummy_decorator2(func):
        def wrapper(*a, **kw):
            res = func(*a, **kw)
            res['test2'] = 'replacement #2'
            return res
        return wrapper

    resource.decorators = [dummy_decorator1, dummy_decorator2]
    resource.create = resource._apply_decorators(resource.create)

    expected_values = {'test1': 'replacement #1', 'test2': 'replacement #2'}
    assert resource.create() == expected_values


def test_is_valid_formatter_positive():
    resource, _, _, _ = create_resource_helper(formatter=formats.JsonFormat)
    assert resource._is_valid_formatter


def test_is_valid_formatter_negative():
    resource, _, _, _ = create_resource_helper(formatter=None)
    assert resource._is_valid_formatter is False


def test_error_formatter_valid():
    resource, _, _, _ = create_resource_helper(formatter=formats.JsonFormat)
    assert resource._error_formatter == formats.JsonFormat


def test_error_formatter_with_unknown_formatter():
    resource, _, _, _ = create_resource_helper(formatter=None)
    assert resource._error_formatter == formats.DEFAULT_FORMATTER


def test_get_method_valid():
    resource, _, _, _ = create_resource_helper()
    type(resource).create = mock.Mock(return_value={})
    assert resource._get_method('create') == resource.create


def test_get_method_with_not_existing_method():
    resource, _, _, _ = create_resource_helper()

    with pytest.raises(errors.BadRequestError) as e:
        resource._get_method('not_exising_method')
    assert 'Method "GET" is not implemented for a given endpoint' in str(e)


def test_get_payload_should_pass_validation():
    resource, _, formatter_mock, _ = create_resource_helper(
        method='PUT', data='data'
    )
    formatter_mock.unserialize.return_value = {'data': 'should be overriden'}

    expected_data = {'data': 'new value'}
    resource.fields = mock.Mock()
    resource.fields.validate.return_value = expected_data

    assert resource._get_payload() == expected_data


def test_get_payload_unexpected_data():
    resource, _, formatter_mock, _ = create_resource_helper(
        method='PUT', data='data'
    )
    formatter_mock.unserialize.side_effect = formats.LoadError()

    with pytest.raises(errors.BadRequestError) as e:
        resource._get_payload()
    assert 'Fail to load the data' in str(e)


def test_get_payload_not_mapable_payload():
    resource, _, formatter_mock, _ = create_resource_helper(
        method='PUT', data='data'
    )
    formatter_mock.unserialize.return_value = ['item']

    with pytest.raises(errors.BadRequestError) as e:
        resource._get_payload()
    assert 'Data should be key -> value structure' in str(e)


def test_get_payload_field_validation_fails():
    resource, _, formatter_mock, _ = create_resource_helper(
        method='PUT', data='data'
    )
    formatter_mock.unserialize.return_value = {'test': 'data'}

    resource.fields = mock.Mock()
    field_error_message = 'Invalid field value'
    resource.fields.validate.side_effect = fields.FieldSet.Error(
        field_error_message
    )

    with pytest.raises(errors.BadRequestError) as e:
        resource._get_payload()
    assert field_error_message in str(e)


def test_get_payload_field_misconfigured_fields_fails():
    resource, _, formatter_mock, _ = create_resource_helper(
        method='PUT', data='data'
    )
    formatter_mock.unserialize.return_value = {'test': 'data'}
    resource.fields = mock.Mock()

    configuration_error_message = 'Improperly configured'
    conf_error = fields.FieldSet.ConfigurationError(
        configuration_error_message
    )
    resource.fields.validate.side_effect = conf_error

    with pytest.raises(errors.ServerError) as e:
        resource._get_payload()
    assert configuration_error_message in str(e)


def test_get_payload_field_validation_no_data_empty_payload():
    resource, _, _, _ = create_resource_helper(method='POST')
    assert {} == resource._get_payload()


def test_get_payload_validation_no_fields_case_empty_payload():
    resource, _, formatter_mock, _ = create_resource_helper(
        method='PUT', data='data'
    )
    formatter_mock.unserialize.return_value = {'data': 'test'}
    assert {} == resource._get_payload()


@patch.object(formats.JsonFormat, 'serialize')
def test_process_valid(serialize_mock):
    mocked_value = 'mocked_value'
    serialize_mock.return_value = mocked_value

    resource, _, _, _ = create_resource_helper(formatter=formats.JsonFormat)
    type(resource).show = mock.Mock(return_value={})
    res = resource.process(iden=10)

    assert res == mocked_value


@patch.object(formats.JsonFormat, 'serialize')
def test_process_valid_list(serialize_mock):
    resource, _, _, _ = create_resource_helper(formatter=formats.JsonFormat)

    serialize_mock.return_value = '[]'
    type(resource).list = mock.Mock(return_value=[])
    res = resource.process()
    assert res == '[]'

    serialize_mock.return_value = '{}'
    resource.show = mock.Mock(return_value={})
    res = resource.process(iden=10)
    assert res == '{}'


def test_process_wrong_formatter():
    resource, _, _, _ = create_resource_helper(formatter=None)
    resource.list = mock.MagicMock(return_value='')

    with pytest.raises(errors.BadRequestError) as e:
        resource.process()
    assert 'Not recognizable format' in str(e)


@patch.object(formats.JsonFormat, 'serialize')
def test_process_method_raising_rest_error(serialize_mock):
    resource, _, _, _ = create_resource_helper(formatter=formats.JsonFormat)
    type(resource).list = mock.Mock(side_effect=errors.RestError('test'))

    with pytest.raises(errors.RestError) as e:
        resource.process()
    assert 'test' in str(e)


@patch.object(formats.JsonFormat, 'serialize')
def test_process_error_in_method_should_raise_server_error(serialize_mock):
    resource, _, _, _ = create_resource_helper(formatter=formats.JsonFormat)
    type(resource).list = mock.MagicMock(
        side_effect=ValueError('I will raise')
    )

    with pytest.raises(ValueError) as e:
        resource.process()
    assert 'I will raise' in str(e)


@patch.object(formats.JsonFormat, 'serialize')
def test_process_error_in_formatter_serialize_should_raise_server_error(
    serialize_mock
):
    resource, _, _, _ = create_resource_helper(formatter=formats.JsonFormat)
    type(resource).list = mock.MagicMock(return_value='')
    serialize_mock.side_effect = formats.LoadError()

    with pytest.raises(errors.ServerError) as e:
        resource.process()
    assert "Service can't respond with this format" in str(e)


@patch.object(Resource, 'process')
def test_dispatch_valid(process_mock):
    args = ('arg1', 'arg2')
    kwargs = {'kw1': 'kw1', 'kw2': 'kw2'}
    expected_result = json.dumps({'res': 'response from process'})
    expected_content_type = 'content/type'

    formatter_mock = mock.Mock(content_type=expected_content_type)
    resource, _, _, _ = create_resource_helper(formatter=formatter_mock)

    process_mock.return_value = expected_result
    res, status, content_type = resource.dispatch(*args, **kwargs)

    resource.process.assert_called_with(*args, **kwargs)
    assert res == expected_result
    assert status == 200
    assert content_type == expected_content_type


@patch.object(Resource, 'process')
def test_dispatch_exception(process_mock):
    resource, _, _, _ = create_resource_helper()
    resource.process.side_effect = errors.ServerError('Error!')

    res, status, content_type = resource.dispatch()
    assert res == json.dumps({'error': 'Error!'})
    assert status == 503
    assert content_type == 'application/json'

    resource.process.side_effect = errors.BadRequestError('Wrong!', code=101)

    res, status, content_type = resource.dispatch()
    assert res == json.dumps({'error': 'Wrong!', 'code': 101})
    assert status == 400
    assert content_type == 'application/json'
