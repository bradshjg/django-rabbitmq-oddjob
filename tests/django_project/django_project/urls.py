from django.urls import include, path

urlpatterns = [
    path("oddjob/", include("django_rabbitmq_oddjob.urls")),
]
