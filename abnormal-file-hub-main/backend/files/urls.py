from django.urls import path
from . import views

urlpatterns = [
    path('files/', views.FileListCreateView.as_view(), name='file-list-create'),
    path('files/<uuid:pk>/', views.FileRetrieveDestroyView.as_view(), name='file-retrieve-destroy'),
    path('storage-stats/', views.StorageStatsView.as_view(), name='storage-stats'),
] 