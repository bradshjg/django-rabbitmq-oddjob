from django.http import HttpResponse, JsonResponse

from django_rabbitmq_oddjob.amqp_transport import AMQPTransport
from django_rabbitmq_oddjob.exceptions import OddjobAuthorizationError, OddjobInvalidResultTokenError



def result(request, result_token):
    """Get the result of an oddjob task using the result token

    Status codes:

    200 - successfully retrieved task result
    204 - task result not yet available
    404 - unauthorized or non-existent task
    """
    transport = AMQPTransport(request)
    try:
        result = transport.get_result(result_token)
    except (OddjobAuthorizationError, OddjobInvalidResultTokenError):
        return HttpResponse(status=404)

    if result:
        return JsonResponse(result)
    # NB it's not obvious, but we return a 204 to unauthorized users while the task is still pending.
    # This isn't intentional, but rather an artifact of the result holding authorization data.
    return HttpResponse(status=204)
