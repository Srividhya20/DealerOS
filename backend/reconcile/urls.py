
from django.urls import path
from . import views

urlpatterns = [
    path(
        "disagreements/",
        views.disagreements_api,
        name="disagreements_api"
    ),
]
