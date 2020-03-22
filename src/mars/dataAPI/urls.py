from django.urls import path, include

from . import views
app_name = 'dataapi'
urlpatterns = [
    #URL: .TLD/api/v1/data
    path('in', views.datain, name='datain'),
    path('out/users', views.dataout_users, name='dataout_users'),
    path('out/device', views.dataout_device, name='dataout_device'),
    path('out/activity', views.dataout_activity, name='dataout_activity'),
    path('out', views.dataout, name='dataout'),

#    path('control', views.control, name='control'),
#    path('status', views.status, name='status'),

]
