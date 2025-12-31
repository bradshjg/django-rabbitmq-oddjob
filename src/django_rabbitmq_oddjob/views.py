from django.http import JsonResponse


def result(request, result_token):
    # Dummy implementation for demonstration purposes
    data = {
        "result_token": result_token,
        "status": "success",
        "data": "This is a dummy response."
    }
    return JsonResponse(data)
