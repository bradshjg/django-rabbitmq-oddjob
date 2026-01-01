from django.urls import include, path

from django_project.views import launch_add_task, run_add_sync

urlpatterns = [
    path("launch_add_task/", launch_add_task),
    path("run_add_sync/", run_add_sync),
    path("oddjob/", include("django_rabbitmq_oddjob.urls")),
]
