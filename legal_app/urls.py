from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_document, name='upload'),
    path('analysis/<uuid:doc_id>/', views.analysis_view, name='analysis'),
    path('api/status/<uuid:doc_id>/', views.api_status, name='api_status'),
    path('api/eli5/<int:clause_id>/', views.eli5_clause, name='eli5_clause'),
]
