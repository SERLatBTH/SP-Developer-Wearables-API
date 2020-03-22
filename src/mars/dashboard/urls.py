from django.urls import path, include

from . import views
app_name = 'dashboard'
urlpatterns = [
    #URL: .TLD/dashboard/
    path('', views.login_user, name='dashboard'),
    #URL: .TLD/dashboard/user   Requires authentication in session
    path('user/', views.user, name='userpage'),
    #URL: .TLD/dashboard/user/123   Requires authentication for user 123
    path('user/<int:user_id>/', views.user, name='userpage'),
    #URL: .TLD/dashboard/admin      Requires authentication and that user is staff
    path('admin/', views.admin, name='adminpage'),
    
    
    path('create_account', views.create_account, name="create_account"),
    path('edit_account', views.edit_account, name="edit_account"),
    path('toggle_active_account', views.toggle_active_account, name="toggle_active_account"),
    
    path('create_user_key', views.create_user_key, name="create_user_key"),
    path('edit_user_key', views.edit_user_key, name="edit_user_key"),
    path('remove_user_key', views.remove_user_key, name="remove_user_key"),
    
    path('add_new_device', views.add_new_device, name="add_new_device"),
    path('edit_user_device', views.edit_user_device, name="edit_user_device"),
    path('remove_user_device', views.remove_user_device, name="remove_user_device"),



    path('login', views.login_user, name='login'),
    path('logout', views.logout_user, name='logout'),

]
