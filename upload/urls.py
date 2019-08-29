from django.urls import path

from . import views

urlpatterns = [
	path('about/', views.about, name='about'),
	path('status/', views.status, name='status'),
	path('', views.upload, name='upload'),
]
