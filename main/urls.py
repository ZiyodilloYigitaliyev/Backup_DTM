from django.urls import path
from .views import ProcessDataView

urlpatterns = [
   path("upload/",  ProcessDataView.as_view(), name="upload"),
]