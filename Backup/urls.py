from .views import BackupDataView
from django.urls import path

urlpatterns = [
    path('backup', BackupDataView.as_view(), name='backup_question')
]