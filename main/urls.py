from django.urls import path
from .views import ProcessedDataViewSet

urlpatterns = [
   path("upload/",  ProcessedDataViewSet.as_view(), name="upload"),
]