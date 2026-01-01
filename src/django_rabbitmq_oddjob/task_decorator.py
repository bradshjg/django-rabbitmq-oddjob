import functools
import threading

from django.http import HttpRequest
from django.urls import reverse

from django_rabbitmq_oddjob.amqp_transport import AMQPTransport


class oddjob:  # noqa N801 - class name lowercase to relfect its usage as a decorator
    """Decorator to mark a function as an oddjob task.

    Usage:

        @oddjob
        def my_task(arg1, arg2, kwarg1=None, kwarg2=None):
            # Task implementation
            pass

    This decorator can be used to register a function as a task that can be executed asynchronously
    in a separate thread.

    To run the task in a separate thread, call the `run_in_thread` method on the decorated function:

        result_url = my_task.run_in_thread(args=(arg1, arg2), kwargs={"kwarg1": kwarg1, "kwarg2": kwarg2}, request=request, public=False)

    The `request` required keyword argument is a Django request object. An optional `public` keyword argument, if set to `True`,
    will allow the result to be read without authentication. Otherwise, only the user who created the task can read the result.
    """

    def __init__(self, wrapped):
        self.wrapped = wrapped
        functools.update_wrapper(self, wrapped)

    def __call__(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)

    def run_in_thread(self, args=(), kwargs=None, *, request: HttpRequest, public=False):
        if kwargs is None:
            kwargs = {}
        transport = AMQPTransport(request)
        result_token = transport.get_result_token()

        thread = threading.Thread(
            target=self._run,
            kwargs={
                "args": args,
                "kwargs": kwargs,
                "result_token": result_token,
                "transport": transport,
                "public": public,
            },
        )
        thread.start()

        path = reverse("oddjob-result", kwargs={"result_token": result_token})
        return request.build_absolute_uri(path)

    def _run(self, *, args=(), kwargs=None, result_token: str, transport: AMQPTransport, public=False):
        if kwargs is None:
            kwargs = {}
        result_data = self.wrapped(*args, **kwargs)
        transport.publish_result(result_token=result_token, result_data=result_data, public=public)
