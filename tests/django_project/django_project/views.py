from django.http import JsonResponse

from django_project.tasks import add

def launch_add_task(request):
    public = request.GET.get("public") == "true"
    sleep = int(request.GET.get("sleep", 0))
    result_url = add.run_in_thread(args=(1, 2), kwargs={"sleep": sleep}, request=request, public=public)
    return JsonResponse({"result_url": result_url})

def run_add_sync(_request):
    return JsonResponse(add(1, 2))
