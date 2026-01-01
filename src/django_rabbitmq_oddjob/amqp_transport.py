

import json
import base64
import typing
from contextlib import contextmanager

from django.conf import settings
from pika import BlockingConnection, URLParameters
from pika.adapters.blocking_connection import BlockingChannel

from django_rabbitmq_oddjob.exceptions import (
    OddjobAuthorizationError,
    OddjobException,
    OddjobInvalidResultTokenError,
)


class AMQPTransport:
    """Handle communication with RabbitMQ for oddjob tasks.

    Pika is generally not thread-safe, each connection must be created in a separate thread.
    """
    DEFAULT_QUEUE_TTL = 300_000  # 5 minutes in milliseconds

    def __init__(self, request):
        self.rabbitmq_url = settings.ODDJOB_SETTINGS["rabbitmq_url"]
        self.queue_ttl = settings.ODDJOB_SETTINGS.get("queue_ttl", self.DEFAULT_QUEUE_TTL)
        self.request = request

    def get_result_token(self) -> str:
        with self._get_channel() as channel:
            try:
                res = channel.queue_declare(queue="", arguments={"x-expires": self.queue_ttl})
            except Exception as e:
                raise OddjobException(f"Failed to get result token") from e

        return self._token_from_queue(res.method.queue)

    def publish_result(self, result_token: str, result_data: dict, public=False) -> None:
        """Publish the result data to RabbitMQ.

        The structure of the published data is as follows:
        {
            "r": <result_data>,
            "u": <username>  # only if not public
        }
        """
        result_data = {
            "r": result_data,
        }
        current_username = self._get_current_username()
        if not public and current_username:
            result_data.update({"u": current_username})

        with self._get_channel() as channel:
            queue_name = self._queue_from_token(result_token)
            try:
                channel.basic_publish(
                    exchange="",
                    routing_key=queue_name,
                    body=json.dumps(result_data),
                )
            except Exception as e:
                raise OddjobException(f"Failed to publish result") from e

    def get_result(self, result_token: str) -> typing.Optional[dict]:
        """Retrieve the result for a given result token.

        A result can only retrieved once. Subsequent calls with the same token will raise
        OddjobInvalidResultTokenError.

        Returns:
            The result data if found and authorized, None if still waiting for a result.

        Raises:
            OddjobInvalidResultTokenError: If the result token is invalid (unknown, expired or
            already consumed).
            OddjobAuthorizationError: If the current user is not authorized to access the result.
        """
        with self._get_channel() as channel:
            queue_name = self._queue_from_token(result_token)
            try:
                method, _properties, body = channel.basic_get(queue=queue_name)
            except Exception as e:
                if hasattr(e, "reply_code") and e.reply_code == 404:
                    raise OddjobInvalidResultTokenError()
                raise OddjobException(f"Failed to get result") from e
            else:
                if not method:
                    return
                data = json.loads(body)
                # there are three cases to handle here:
                #
                # 1. No auth required: delete queue and return result
                # 2. Auth required, current user is the owner: delete queue and return result
                # 3. Auth required, current user is not the owner: raise authorization error and requeue
                if not data.get("u"):
                    # Case 1: No auth required
                    channel.queue_delete(queue=queue_name)
                    return data["r"]
                else:
                    # Case 2 and 3: Auth required
                    required_username = data["u"]
                    current_username = self._get_current_username()
                    if current_username != required_username:
                        channel.basic_nack(method.delivery_tag, requeue=True)
                        raise OddjobAuthorizationError()
                    else:
                        channel.queue_delete(queue=queue_name)
                        return data["r"]

    @contextmanager
    def _get_channel(self) -> typing.Generator[BlockingChannel]:
        connection = BlockingConnection(
            URLParameters(settings.ODDJOB_SETTINGS["rabbitmq_url"])
        )
        try:
            yield connection.channel()
        finally:
            connection.close()

    def _get_current_username(self) -> typing.Optional[str]:
        if not hasattr(self.request, "user"):
            return
        return self.request.user.get_username()

    def _token_from_queue(self, queue_name: str) -> str:
        """Generate a result token from a RabbitMQ queue name."""
        return base64.urlsafe_b64encode(queue_name.encode()).decode()

    def _queue_from_token(self, result_token: str) -> str:
        """Retrieve the RabbitMQ queue name from a result token."""
        try:
            return base64.urlsafe_b64decode(result_token.encode()).decode()
        except Exception as e:
            raise OddjobInvalidResultTokenError
