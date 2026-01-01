import functools
import threading


class oddjob:
    """Decorator to mark a function as an oddjob task.

    Usage:

        @oddjob
        def my_task(arg1, arg2, kwarg1=None, kwarg2=None):
            # Task implementation
            pass

    This decorator can be used to register a function as a task that can be executed asynchronously
    in a separate thread.

    To run the task in a separate thread, call the `async` method on the decorated function:

        result_url = my_task.async(args=(arg1, arg2), kwargs={"kwarg1": kwarg1, "kwarg2": kwarg2}, request=request, public=False)

    The `request` keyword argument is required to associate the task with the current user unless
    `public=True`. An `public` keyword argument, if set to `True`, will allow the result to be read without
    authentication. Otherwise, only the user who created the task can read the result.
    """

    def __init__(self, wrapped):
        self.wrapped = wrapped
        functools.update_wrapper(self, wrapped)

    def __call__(self, args=(), kwargs={}, *, request=None, public=False):
        result_token = self._generate_result_token()
        thread = threading.Thread(
            target=self._run_task,
            args=(result_token, public) + args,
            kwargs=kwargs,
        )
        thread.start()

        return self.wrapped(*args, **kwargs)

    def _generate_result_token(self):
        import uuid

        return str(uuid.uuid4())
