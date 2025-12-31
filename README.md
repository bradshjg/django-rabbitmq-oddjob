# django-rabbitmq-oddjob

Oddjob fulfills a very narrow use case. It supports the ability to offload tasks to threads and retrieve the results of those tasks over HTTP. The temporary storage of task results is mediated by RabbitMQ.

If you have a task you want to (rarely) run outside the request/response cycle and have a RabbitMQ broker but no database, this might be a fit. But probably not :-)

The narrow use case this fit was an internal Django project with no existing database but access to a centrally supported RabbitMQ service. Most work fit within the request/response cycle, but not _all_ of it. So we toss that work onto a separate thread and poll for completion on the client-side.

Goals:

* No extra proceses/workers to manage (threads are spun off ad-hoc)
* Automatic cleanup (queue TTLs ensure queues are deleted even if results are never read)
* Support optional security via Django user model (only return results to a specific user)

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

The decorated functions can be called normally (which will block as if it were undecorated), or called via the `async` method which will return the url to poll for the result. The `async` method takes an optional `oddjob_username` parameter. If supplied, the result will only be returned if the `request.user.username` matches the supplied value (otherwise a 404 will be returned).

```python
import time

import requests

from django_rabbitmq_oddjob import oddjob

@oddjob
def add(x: int, y: int) -> dict[str, int]:
    return {
        "x": x,
        "y": y,
        "sum": x + y
    }

result_url = add.async(1, 2, oddjob_username="some_user")

# poll for result
resp_status = None
while resp_status != 200:
    resp = request.get(result_url, auth=("some_user", "some_password"))
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
