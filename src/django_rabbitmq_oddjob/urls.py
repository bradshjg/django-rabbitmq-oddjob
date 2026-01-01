from django.urls import path

from . import views

urlpatterns = [
    path("result/<str:result_token>/", views.result, name="oddjob-result"),
]
