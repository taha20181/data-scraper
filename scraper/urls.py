from django.urls import path
from .views import dashboard_view, list_view, export

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("list/", list_view, name="list"),
    path("export/", export, name="export"),
]