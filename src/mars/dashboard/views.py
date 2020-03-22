from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseRedirect, HttpResponseBadRequest, HttpRequest
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .forms import UserAPICreate, CreateAccount, NewDevice, EditAccount
from .models import Api, Device
from dataAPI.models import Data
from activityAPI.models import Activity
import secrets
import datetime

def index(request):
    return HttpResponse("Hello world, dashboard_index page")

def user(request, user_id = -1):
    #Not an authenticated user
    if not request.user.is_authenticated:
        raise PermissionDenied
    #Use user_id connected to session_id as default,
    #Check if sessioned user is staff and change user to user_id argument
    #else, 403
    user = request.user.id
    if request.user.is_staff:
        if user_id != -1:
            user = user_id
    else:
        if user_id != -1 and user_id != request.user.id:
            raise PermissionDenied

    user_item = User.objects.filter(id=user)[0]
    
    #get api keys from db for selected user
    api_keys_list = Api.objects.filter(user_id=user)
    #get devices from db for selected user
    device_list = Device.objects.filter(user_id=user)
    template = loader.get_template('dashboard/user.html')
    context = {
        'api_keys_list': api_keys_list,
        'user_item': user_item,
        'device_list': device_list,
    }
    return HttpResponse(template.render(context, request))

def time_date_object(time_string):
    time = None
    try:
        #fromisoformat() requires python3.7 or higher. No Z at the end of the string!
        time = datetime.datetime.fromisoformat(time_string)
    except:
        time = None
    return time

def admin(request):
    #Not an authenticated staff user
    if not request.user.is_authenticated or not request.user.is_staff:
        raise PermissionDenied
    users_list = User.objects.all()
    user = request.user.id
    api_keys_list = Api.objects.filter(user_id=user,admin_access=1)
    template = loader.get_template('dashboard/admin.html')
    
    filter_status_text = "All users"
    user_text = None
    user_id = -1
    if request.GET.get("user_filter") is not None:
        try:
            user_id = int(request.GET.get("user_filter"))
            if len(User.objects.filter(id=user_id)) > 0:
                user_text = "User " + User.objects.filter(id=user_id)[0].username
        except:
            user_id = -1
    

    time_start_string = None
    filter_start = None
    if request.GET.get("filter_start") is not None:
        filter_start = time_date_object(request.GET.get("filter_start"))
        if filter_start is not None:
            time_start_string = ": " + filter_start.strftime('%Y-%m-%d')
    time_end_string = None
    filter_end = None
    if request.GET.get("filter_end") is not None:
        filter_end = time_date_object(request.GET.get("filter_end"))
        if filter_end is not None:
            time_end_string = filter_end.strftime('%Y-%m-%d')
    
    if user_text is not None:
        filter_status_text = user_text
    filter_status_text += ": "
    if time_start_string is not None:
        filter_status_text += time_start_string
    filter_status_text += " - "
    if time_end_string is not None:
        filter_status_text += time_end_string


    numbr_of_data_points = Data.objects.filter()
    numbr_of_activities = Activity.objects.filter()
    numbr_of_devices = Device.objects.filter()
    
    if user_id != -1:
        numbr_of_data_points = numbr_of_data_points.filter(user_id=user_id)
        numbr_of_activities = numbr_of_activities.filter(user_id=user_id)
        numbr_of_devices = numbr_of_devices.filter(user_id=user_id)
    
    if filter_end is not None:
        numbr_of_data_points = numbr_of_data_points.filter(time_added__date__lte=filter_end)
        numbr_of_activities = numbr_of_activities.filter(time_started__date__lte=filter_end)

    if filter_start is not None:
        numbr_of_data_points = numbr_of_data_points.filter(time_added__date__gte=filter_start)
        numbr_of_activities = numbr_of_activities.filter(time_started__date__gte=filter_start)
    
    if filter_start is not None and filter_end is not None:
        if filter_start > filter_end:
            numbr_of_data_points = 0
            numbr_of_activities = 0
        else:
            numbr_of_data_points = numbr_of_data_points.count()
            numbr_of_activities = numbr_of_activities.count()
    else:    
        numbr_of_data_points = numbr_of_data_points.count()
        numbr_of_activities = numbr_of_activities.count()
    numbr_of_devices = numbr_of_devices.count()

   # return HttpResponse(numbr_of_data_points)

    context = {
        'users_list': users_list,
        'api_keys_list': api_keys_list,
        'filter_status_text': filter_status_text,
        'numbr_of_data_points': numbr_of_data_points,
        'numbr_of_activities': numbr_of_activities,
        'numbr_of_devices': numbr_of_devices,
    }
    return HttpResponse(template.render(context, request))

def create_account(request):
    if not request.user.is_authenticated and not request.user.is_staff:
        raise PermissionDenied
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    else:
        form = CreateAccount(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['fname']
            last_name = form.cleaned_data['lname']
            is_staff = form.cleaned_data['staff_checkbox']

            new_user = User.objects.create(username=username, first_name=first_name, last_name=last_name, is_staff=is_staff)
            new_user.set_password(password)
            new_user.save()
            return HttpResponseRedirect('admin')
        else:
            return HttpResponseBadRequest()

def edit_account(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    else:
        form = EditAccount(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['fname']
            last_name = form.cleaned_data['lname']
            is_staff = form.cleaned_data['staff_checkbox']
            user_id = form.cleaned_data['user_id']
            if user_id:
                if request.user.id != user_id and not request.user.is_staff:
                    raise PermissionDenied
                user_item = User.objects.filter(id=user_id)[0]
                if password:
                    if len(password) < 8:
                        return HttpResponseBadRequest()
                    user_item.set_password(password)
                user_item.username = username
                user_item.first_name = first_name
                user_item.last_name = last_name
                if request.user.is_staff and is_staff:
                    user_item.is_staff = is_staff
                user_item.save()
                #if password has been set for the current session user
                #return to login page instead of referer since all session for that user is reset, requiring a new login
                if password and user_item.id == request.user.id:
                    return HttpResponseRedirect('login')
                if request.META['HTTP_REFERER']:
                    return HttpResponseRedirect(request.META['HTTP_REFERER'])
                #if unknown where request came from, use .TLD/dashboard
                return HttpResponseRedirect('.')
        return HttpResponseBadRequest()

def toggle_active_account(request):
    if not request.user.is_authenticated and not request.user.is_staff:
        raise PermissionDenied
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    else:
        user_id = request.POST['user_id']
        user_item = User.objects.filter(id=user_id)[0]
        if user_item.is_active == 1:
            user_item.is_active = 0
        else:
            user_item.is_active = 1
        user_item.save()
        return HttpResponseRedirect('admin')


def create_user_key(request):
    return_id = request.user.id
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    else:
        form = UserAPICreate(request.POST)
        #validate input
        if form.is_valid():
            name = form.cleaned_data['name']
            write_permission = form.cleaned_data['write_checkbox']
            read_permission = form.cleaned_data['read_checkbox']
            user_id = form.cleaned_data['user_id']
            
            global_api = request.POST.get('global_api')
            admin_access = 0
            if global_api is not None and request.user.is_staff:
                if global_api == "true":
                    #global_api was set to true and user is staff, create Global API key
                    admin_access = 1

            #if user_id wasn't set, set it to return_id
            if not user_id:
                user_id = return_id
            #if user_id and session user aren't the same, check if the session user is staff, if they are, allow changes to other user
            if user_id != request.user.id and request.user.is_staff:
                return_id = user_id    
            new_api_key = secrets.token_hex(10)
            new_api_item = Api(key=new_api_key, name=name, write_access=write_permission, read_access=read_permission, admin_access=admin_access, user_id=return_id)
            new_api_item.save()
            #timing based attacks mitigated with below function (use tolower function?)
            #secrets.compare_digest(a, b)
            if return_id != request.user.id:
                return HttpResponseRedirect('user/%d' % return_id)
            return HttpResponseRedirect('user')
        else:
            return HttpResponseBadRequest()

def edit_user_key(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    else:
        form = UserAPICreate(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            write_permission = form.cleaned_data['write_checkbox']
            read_permission = form.cleaned_data['read_checkbox']
            key_id = request.POST['key_id']
            key_item = Api.objects.filter(id=key_id)[0]
            if key_item.user_id != request.user.id and not request.user.is_staff:
                raise PermissionDenied
            key_item.name = name
            key_item.write_access = write_permission
            key_item.read_access = read_permission
            key_item.save()
            if key_item.user_id != request.user.id:
                return HttpResponseRedirect('user/%d' % key_item.user_id)
            return HttpResponseRedirect('user')
        else:
            return HttpResponseBadRequest()

def remove_user_key(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    else:
        key_id = request.POST['key_id']
        key_item = Api.objects.filter(id=key_id)[0]
        if key_item.user_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied
        key_item.delete()
        if key_item.user_id != request.user.id:
            return HttpResponseRedirect('user/%d' % key_item.user_id)
        return HttpResponseRedirect('user')



def add_new_device(request):
    return_id = request.user.id
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    else:
        form = NewDevice(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            d_type = form.cleaned_data['d_type']
            user_id = form.cleaned_data['user_id']
            if not user_id:
                user_id = return_id
            if user_id != request.user.id and request.user.is_staff:
                return_id = user_id    
            new_device = Device(name=name, device_type=d_type, user_id=return_id)
            new_device.save()
            if return_id != request.user.id:
                return HttpResponseRedirect('user/%d' % return_id)
            return HttpResponseRedirect('user')
        else:
            return HttpResponseBadRequest()

def edit_user_device(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    else:
        form = NewDevice(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            d_type = form.cleaned_data['d_type']
            device_id = form.cleaned_data['device_id']
            device_item = Device.objects.filter(id=device_id)[0]

            if device_item.user_id != request.user.id and not request.user.is_staff:
                raise PermissionDenied
            device_item.name = name
            device_item.device_type = d_type
            device_item.save()
            if device_item.user_id != request.user.id:
                return HttpResponseRedirect('user/%d' % device_item.user_id)
            return HttpResponseRedirect('user')
        else:
            return HttpResponseBadRequest()

def remove_user_device(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    else:
        device_id = request.POST['device_id']
        device_item = Device.objects.filter(id=device_id)[0]
        if device_item.user_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied
        device_item.delete()
        if device_item.user_id != request.user.id:
            return HttpResponseRedirect('user/%d' % device_item.user_id)
        return HttpResponseRedirect('user')


def login_user(request):
    if request.method != "POST":
        if request.user.is_authenticated:
            if request.user.is_staff:
                return HttpResponseRedirect('admin')
            else:
                return HttpResponseRedirect('user')
        return render(request, 'dashboard/login.html')
    else:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if request.user.is_staff:
                return HttpResponseRedirect('admin')
            else:
                return HttpResponseRedirect('user')
        else:
            context = {
                'message': 'Incorrect username or password'
            }
            return render(request, 'dashboard/login.html', context)

def logout_user(request):
    logout(request)
    return HttpResponseRedirect('login')
