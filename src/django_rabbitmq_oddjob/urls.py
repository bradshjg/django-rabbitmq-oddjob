from django.urls import path

from django_rabbitmq_oddjob import views

urlpatterns = [
    path("result/<str:result_token>/", views.result, name="oddjob-result"),
]
