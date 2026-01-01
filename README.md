# django-rabbitmq-oddjob

Oddjob fulfills a very narrow use case. It supports the ability to offload tasks to threads and retrieve the results of those tasks over HTTP. The temporary storage of task results is mediated by RabbitMQ.

If you have a task you want to (rarely) run outside the request/response cycle and have a RabbitMQ broker but no database, this might be a fit. But probably not :-)

The narrow use case this fit was an internal Django project with no existing database but access to a centrally supported RabbitMQ service. Most work fit within the request/response cycle, but not _all_ of it. So we toss that work onto a separate thread and poll for completion on the client-side.

Goals:

* No extra proceses/workers to manage (threads are spun off ad-hoc)
* Automatic cleanup (queue TTLs ensure queues are deleted even if results are never read)
* Default security via Django user model (only return results to calling user)

Non-goals:

* Not robust to transient network issues or web worker termination, assumes clients can retry
* No concurrency control, assumes low volume usage

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

This project is too absurd to publish, you'll need to vendor it if you want to use it.

## Usage

### Configuration

In Django settings, include `django_rabbitmq_oddjob` as an installed app and supply `ODDJOB_SETTINGS`

```python
INSTALLED_APPS = [
    "django_rabbitmq_oddjob",
    ...,
]

ODDJOB_SETTINGS = {
    "rabbitmq_url": "amqp://guest:guest@rabbitmq:5672/%2F",  # See https://pika.readthedocs.io/en/stable/modules/parameters.html#urlparameters
    "queue_ttl": 300  # queue time-to-live (in seconds), default is 5 minutes.
}

...
```

In your urlconf, include

```python
urlpatterns = [
    path("oddjob/", include("django_rabbitmq_oddjob.urls")),
    ...,
]
```

### Tasks

Tasks are functions decorated with `@oddjob` that must return a JSON-serializable value.

The decorated functions can be called normally (as if it were undecorated), or called via an `run_in_thread` method which will return the url to poll for the result. The `run_in_thread` method signature is

```python
decorated_function.run_in_thread(args=(), kwargs={}, *, request, public=False) -> str
```

`args` and `kwargs` are passed transparently to the wrapped function. `request` is the Django request object. `public` is a boolean that controls whether fetching the result requires that the `request.user.username` for the current request matches that of the initial `run_in_thread` call.


`tasks.py`
```python
from django_rabbitmq_oddjob import oddjob

@oddjob
def add(x: int, y: int) -> dict[str, int]:
    return {
        "x": x,
        "y": y,
        "sum": x + y
    }
```

`views.py`
```python
from django.http import JSONResponse

from tasks import add

def launch_add_task(request):
    result_url = add.run_in_thread(args=(1, 2), request=request)
    return JSONResponse({"result_url": result_url})
```

`poll.py`
```python
import time

import requests

# launch task
resp = request.post("/path/to/launch/add/task/")
resp.raise_for_status()
result_url = resp.json()["result_url"]

# poll for result
resp_status = None
while resp_status != 200:
    resp = request.get(result_url)
    resp.raise_for_status()
    resp_status = resp.status_code
    if resp_status == 200:
        result = resp.json()
        break
    time.sleep(1)

print(result)
# {"x": 1, "y": 2, "sum": 3}
```

## License

`django-rabbitmq-oddjob` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
