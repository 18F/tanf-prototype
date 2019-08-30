from django.urls import path

from . import views

urlpatterns = [
	path('about/', views.about, name='about'),
	path('status/', views.status, name='status'),
	path('fileinfo/<file>/', views.fileinfo, name='fileinfo'),
	path('deletesuccessful/', views.deletesuccessful, name='deletesuccessful'),
	path('delete/<file>/', views.delete, name='delete'),
	path('delete/<file>/<confirmed>', views.delete, name='delete'),
	path('', views.upload, name='upload'),
]
