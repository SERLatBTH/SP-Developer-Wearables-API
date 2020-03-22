from django.urls import path, include

from . import views
app_name = 'api'
urlpatterns = [
    #URL: .TLD/api/v1/
    path('control', views.control, name='control'),
    path('status', views.status, name='status'),

]
