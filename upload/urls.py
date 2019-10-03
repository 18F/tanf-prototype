from django.urls import path

from . import views

urlpatterns = [
    path('about/', views.about, name='about'),
    path('status/', views.status, name='status'),
    path('fileinfo/<file>/', views.fileinfo, name='fileinfo'),
    path('deletesuccessful/', views.deletesuccessful, name='deletesuccessful'),
    path('delete/<file>/', views.delete, name='delete'),
    path('delete/<file>/<confirmed>', views.delete, name='delete'),
    path('viewtables/', views.viewTables, name='viewtables'),
    path('viewquarter/', views.viewquarter, name='viewquarter'),
    path('download/<file>', views.download, name='download'),
    path('download/<file>/<json>/', views.download, name='download'),
    path('useradmin', views.useradmin, name='useradmin'),
    path('logout', views.logout_view, name='logout'),
    path('', views.upload, name='upload'),
]
