import base64
import pytest
from typing import Generator
from unittest import mock

from pika.adapters.blocking_connection import BlockingChannel

from django_rabbitmq_oddjob.amqp_transport import AMQPTransport
from django_rabbitmq_oddjob.exceptions import OddjobInvalidResultTokenError, OddjobAuthorizationError

@pytest.fixture
def transport(rf, django_user_model) -> Generator[AMQPTransport]:
    user = django_user_model.objects.create_user(username="someuser", password="somepassword")
    request = rf.get("/")
    request.user = user
    transport = AMQPTransport(request=request)
    yield transport


def test_get_result_token_creates_auto_named_queue_with_default_ttl(mocker, transport):
    queue_declare_spy = mocker.spy(BlockingChannel, "queue_declare")
    token = transport.get_result_token()
    assert token is not None
    queue_declare_spy.assert_called_once()
    queue_declare_kwargs = queue_declare_spy.mock_calls[0].kwargs
    expected_kwargs = {
        "queue": "",
        "arguments": {"x-expires": transport.DEFAULT_QUEUE_TTL},
    }
    assert queue_declare_kwargs == expected_kwargs


def test_get_result_token_creates_auto_named_queue_with_custom_ttl(mocker, rf, settings):
    expected_queue_ttl = 600_000  # 10 minutes in milliseconds
    new_oddjob_settings = settings.ODDJOB_SETTINGS.copy()
    new_oddjob_settings.update({"queue_ttl": expected_queue_ttl})
    settings.ODDJOB_SETTINGS = new_oddjob_settings

    transport = AMQPTransport(request=rf.get("/"))

    queue_declare_spy = mocker.spy(BlockingChannel, "queue_declare")
    token = transport.get_result_token()
    assert token is not None
    queue_declare_spy.assert_called_once()
    queue_declare_kwargs = queue_declare_spy.mock_calls[0].kwargs
    expected_kwargs = {
        "queue": "",
        "arguments": {"x-expires": expected_queue_ttl},
    }
    assert queue_declare_kwargs == expected_kwargs

def test_get_result_for_nonexistent_token_raises_result_token_error(transport):
    # invalid encoding
    with pytest.raises(OddjobInvalidResultTokenError):
        transport.get_result(result_token="non_existent")

    # invalid queue
    with pytest.raises(OddjobInvalidResultTokenError):
        transport.get_result(result_token=base64.urlsafe_b64encode(b"non_existent").decode())

def test_get_public_result_requires_no_auth(transport, rf):
    token = transport.get_result_token()
    expected_data = {"some": "data"}
    transport.publish_result(token, expected_data, public=True)

    anon_transport = AMQPTransport(request=rf.get("/"))

    res = anon_transport.get_result(token)
    assert res == expected_data

def test_get_private_result_requires_same_publisher_and_fetcher(transport, rf):
    token = transport.get_result_token()
    expected_data = {"some": "data"}
    transport.publish_result(token, expected_data)

    anon_transport = AMQPTransport(request=rf.get("/"))

    # raises for unauthorized user
    with pytest.raises(OddjobAuthorizationError):
        anon_transport.get_result(token)

    # result can still be fetched by authorized user
    res = transport.get_result(token)
    assert res == expected_data

def test_result_can_only_be_fetched_once(transport):
    token = transport.get_result_token()
    expected_data = {"some": "data"}
    transport.publish_result(token, expected_data)
    res = transport.get_result(token)
    assert res == expected_data

    with pytest.raises(OddjobInvalidResultTokenError):
        transport.get_result(token)
