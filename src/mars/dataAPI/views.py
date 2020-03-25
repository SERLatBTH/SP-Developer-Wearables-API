from django.shortcuts import render
from django.utils import dateparse, crypto
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse, HttpRequest
import hmac
import datetime
from django.views.decorators.csrf import csrf_exempt
#import logging
import json
from django.contrib.auth.models import User
from dashboard.models import Api, Device
from activityAPI.models import Activity, GitRepo, GitCommit
from .models import Data

#Error codes
#100 = Invalid API key or user id
#101 = Invalid API permissions
#102 = Invalid API key (Global keys)
#200 = No activity available
#201 = Wrong activity_id in request
#300 = General server error
#301 = Invalid parameter used
#302 = Malformed request
#303 = device doesnt belong to user
#304 = device_id doesn't exist
#400 = JSON not valid

#const "variables"
def READ_PERMISSION(): return 1
def WRITE_PERMISSION(): return 2
def READ_WRITE_PERMISSION(): return 3

def statusCode(errors):
    if 201 in errors or 301 in errors or 302 in errors or 304 in errors or 400 in errors:
        return 400
    elif 100 in errors or 102 in errors:
        return 401
    elif 101 in errors or 303 in errors:
        return 403
    elif 200 in errors:
        return 424
    else:
        return 500

def validate_headers_in(request):
    #Check that all headers are set
    #That API key and user_id matches and that the permission of the API key is correct
    #Checks that there is an active activity for the user
    #Check that the device belongs to the user
    errors = []
    try:
        #Required headers
        user_id      = int(request.headers.get('USER-ID'))
        api_key      = request.headers.get('API-KEY')
        device_id    = int(request.headers.get('DEVICE-ID'))
        activity_id  = int(request.headers.get('ACTIVITY-ID'))
        type_of_data = request.headers.get('TYPE')
    except:
        #Malformed request
        errors.append(302)
    if len(errors) == 0:
        #Check if headers are set
        if (user_id      == None or
            api_key      == None or
            device_id    == None or
            activity_id  == None or
            type_of_data == None):
            #Malformed request
            errors.append(302)
        else:
            if len(Api.objects.filter(user_id=user_id, key=api_key)) == 0:
                #incorrect user_id or api_key
                errors.append(100)
            elif not Api.objects.filter(user_id=user_id, key=api_key)[0].write_access:
                #incorrect api permissions
                errors.append(101)
            else:
                if len(Activity.objects.filter(user_id=user_id, active=True)) > 0:
                    #Active activity exists
                    if activity_id != Activity.objects.filter(user_id=user_id, active=True)[0].id:
                        #Wrong activity_id in request
                        errors.append(201)
                else:
                    #No active activity, return stop signal
                    errors.append(200)
            if len(Device.objects.filter(id=device_id)) > 0:
                if user_id != Device.objects.filter(id=device_id)[0].user_id:
                    #device_id doesn't belong to user
                    errors.append(303)
            else:
                errors.append(304)

    return errors

def validate_json(request):
    errors = []
    #Test if valid JSON or catch error
    try:
        json.loads(request.body.decode('utf-8'))
    except:
        errors.append(400)
    return errors


@csrf_exempt
def datain(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    else:
        #validate headers
        errors  = validate_headers_in(request)
        errors += validate_json(request)
        continue_activity = False
        if len(errors) == 0:
            continue_activity = True
            #Required headers
            user_id      = int(request.headers.get('USER-ID'))
            api_key      = request.headers.get('API-KEY')
            device_id    = int(request.headers.get('DEVICE-ID'))
            activity_id  = int(request.headers.get('ACTIVITY-ID'))
            type_of_data = request.headers.get('TYPE')
            json_data    = request.body.decode('utf-8')
            #Add data to database
            new_data = Data(device_id=device_id, activity_id=activity_id, user_id=user_id, type_of_data=type_of_data, data=json_data)
            new_data.save()
        elif len(errors) == 1 and 200 in errors:
            errors = []
        
        #Response
        if len(errors) > 0:
            return JsonResponse({"success": False, "errors": errors, "continue": continue_activity}, status=statusCode(errors))
        else:
            return JsonResponse({"success": True, "errors": errors, "continue": continue_activity})


def validate_api_key(request, permissions):
    errors = []
    #Required header
    api_key = request.headers.get('API-KEY')
    user_id = request.headers.get('USER-ID')
    #Check if api_key and user_id header is set, if it exists in the db and if it has the correct permissions
    if (api_key == None or user_id == None):
        #Malformed request
        errors.append(302)
    else:
        api_objects = Api.objects.filter(user_id=user_id)
        if len(api_objects) == 0:
            #incorrect user_id
            errors.append(100)
        else:
            api_key_index = -1
            for index, api_object in enumerate(api_objects):
                # constant time function to avoid timing attacks against API key
                if hmac.compare_digest(str(api_object.key), str(api_key)):
                    api_key_index = index
            if api_key_index == -1:
                errors.append(100)
            elif api_objects[api_key_index].admin_access:
                if permissions == READ_PERMISSION():
                    if not api_objects[api_key_index].read_access:
                        errors.append(101)
                elif permissions == WRITE_PERMISSION():
                    if not api_objects[api_key_index].write_access:
                        errors.append(101)
                elif permissions == READ_WRITE_PERMISSION():
                    if not api_objects[api_key_index].read_access and not api_objects[api_key_index].write_access:
                        errors.append(101)
                else:
                    #incorrect api permissions
                    errors.append(101)
            else:
                #incorrect api permissions
                errors.append(101)
    return errors

def stringify_user_info(users):
    user_id, name, privilege = [], [], []
    for user in users:
        user_id.append(user.id)
        name.append(user.username)
        if user.is_staff:
            privilege.append("admin")
        else:
            privilege.append("user")

    user_objects = [{"user_id": uid,"username": un, "privilege": pr} for uid, un, pr in zip(user_id, name, privilege)]
    return user_objects

@csrf_exempt
def dataout_users(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(['GET'])
    else:
        """
    def READ_PERMISSION(): return 1
    def WRITE_PERMISSION(): return 2
    def READ_WRITE_PERMISSION(): return 3
    """
        errors  = validate_api_key(request, READ_PERMISSION())
        user_json = []
        if len(errors) == 0:
            users = User.objects.all()
            user_json = stringify_user_info(users)
    #Response
    if len(errors) > 0:
        return JsonResponse({"success": False, "errors": errors, "users": user_json}, status=statusCode(errors))
    else:
        return JsonResponse({"success": True, "errors": errors, "users": user_json})


def stringify_device_info(devices):
    device_id, device_name, device_type, user_id, time_added = [], [], [], [], []
    for device in devices:
        device_id.append(device.id)
        device_name.append(device.name)
        device_type.append(device.device_type)
        user_id.append(device.user_id)
        time_added.append(device.time_added)
    device_objects = [{"device_id": did, "name": dn, "type": dt, "user_id": uid, "time_added": ta}
                    for did, dn, dt, uid, ta in zip(device_id, device_name, device_type, user_id, time_added)]
    return device_objects

@csrf_exempt
def dataout_device(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(['GET'])
    else:
        allowed_params = ["id", "name", "device_type", "user_id"]
        errors  = validate_api_key(request, READ_PERMISSION())
        param_dictionary = {}

        for param in request.GET.dict():
            if param in allowed_params:
                if request.GET.get(param):
                    if param == "id" or param == "user_id":
                        try:
                            param_dictionary[param] = int(request.GET.get(param))
                        except:
                            #Value is malformed
                            errors.append(302)
                    else:
                        param_dictionary[param] = request.GET.get(param)
                else:
                    #param exists but has no value set
                    errors.append(302)
            else:
                #error, invalid get param
                errors.append(301)

        device_json = []
        if len(errors) == 0:
            #Filter request
            device_list = Device.objects.filter(**param_dictionary)
            device_json = stringify_device_info(device_list)
        
        #Response
        if len(errors) > 0:
            return JsonResponse({"success": False, "errors": errors, "devices": device_json}, status=statusCode(errors))
        else:
            return JsonResponse({"success": True, "errors": errors, "devices": device_json})


def stringify_activity_info(activities):
    activity_id, user_id, device_id, type_of_data, active, time_start, time_end = [], [], [], [], [], [], []
    for activity in activities:
        activity_id.append(activity.id)
        user_id.append(activity.user_id)
        device_id.append(activity.device_id)
        type_of_data.append(activity.activity_type)
        time_start.append(activity.time_started)
        time_end.append(activity.time_ended)

        if activity.active:
            active.append(True)
        else:
            active.append(False)

    activity_objects = [{"activity_id": aid,"user_id": uid, "device_id": did, "type": tpe, "active": act, "time_start": t_start, "time_end": t_end}
                        for aid, uid, did, tpe, act, t_start, t_end in zip(activity_id, user_id, device_id, type_of_data, active, time_start, time_end)]
    return activity_objects

def git_parser(git_params, request):
    repos = []
    commits = []
    return_list = []

    if "repo" in git_params:
        repos = list(GitRepo.objects.filter(name=request.GET.get("repo")).values_list('activity_id', flat=True))
    if "commit" in git_params:
        commits = list(GitCommit.objects.filter(name=request.GET.get("commit")).values_list('activity_id', flat=True))
    #make unique list of activity_ids depending on what params were included
    if "repo" in git_params and "commit" in git_params:
        return_list = list(set(repos) & set(commits))
    elif "repo" in git_params:
        return_list = list(set(repos))
    elif "commit" in git_params:
        return_list = list(set(commits))
    return return_list

def time_date_object(time_string):
    time = None
    try:
        #fromisoformat() requires python3.7 or higher. No Z at the end of the string!
        time = datetime.datetime.fromisoformat(time_string)
    except:
        time = None
    return time


@csrf_exempt
def dataout_activity(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(['GET'])
    else:
        allowed_params = ["id", "user_id", "device_id", "activity_type", "repo", "commit", "active", "time_start", "time_end"]
        errors  = validate_api_key(request, READ_PERMISSION())
        git_params = []
        param_dictionary = {}
        time_start = None
        time_end = None
        for param in request.GET.dict():
            if param in allowed_params:
                if request.GET.get(param):
                    if param == "commit" or param == "repo":
                        git_params.append(param)
                    elif param == "time_start":
                        time_start = request.GET.get(param)
                    elif param == "time_end":
                        time_end = request.GET.get(param)
                    else:
                        if param == "id" or param == "user_id" or param == "device_id":
                            try:
                                param_dictionary[param] = int(request.GET.get(param))
                            except:
                                #Value is malformed
                                errors.append(302)
                        elif param == "active":
                            if request.GET.get(param).lower() in ['true', '1']:
                                param_dictionary[param] = 1
                            elif request.GET.get(param).lower() in ['false', '0']:
                                param_dictionary[param] = 0
                            else:
                                errors.append(302)
                        else:
                            param_dictionary[param] = request.GET.get(param)
                else:
                    #param exists but has no value set
                    errors.append(302)
            else:
                #error, invalid get param
                errors.append(301)
        git_act_id = None
        if len(git_params) > 0:
            #get activity ids for the params and store in list, used to filter request later
            git_act_id = git_parser(git_params, request)
        
        if time_start:
            time_start = time_date_object(time_start)
            if not time_start:
                #Couldn't parse date/time string
                errors.append(302)
        if time_end:
            time_end = time_date_object(time_end)
            if not time_end:
                #Couldn't parse date/time string
                errors.append(302)

        activity_json = []
        if len(errors) == 0:
            #Filter request
            activity_list = Activity.objects.filter(**param_dictionary)
            if git_act_id is not None:
                activity_list = activity_list.filter(pk__in=git_act_id)
            if time_start:
                activity_list = activity_list.filter(time_started__gte=time_start)
            if time_end:
                activity_list = activity_list.filter(time_ended__lte=time_end)
            activity_json = stringify_activity_info(activity_list)
        
        #Response
        if len(errors) > 0:
            return JsonResponse({"success": False, "errors": errors, "activities": activity_json}, status=statusCode(errors))
        else:
            return JsonResponse({"success": True, "errors": errors, "activities": activity_json})


def device_parser(device_params, request):
    return_list = []
    if "device_name" in device_params and "device_type" in device_params:
        return_list = list(set(Device.objects.filter(name=request.GET.get("device_name"), device_type=request.GET.get("device_type")).values_list('id', flat=True)))
    elif "device_name" in device_params:
        return_list = list(set(Device.objects.filter(name=request.GET.get("device_name")).values_list('id', flat=True)))
    elif "device_type" in device_params:
        return_list = list(set(Device.objects.filter(device_type=request.GET.get("device_type")).values_list('id', flat=True)))
    return return_list

def activity_parser(activity_params, request):
    return_list = []
    active_var = None
    if "active" in activity_params:
        if request.GET.get("active").lower() in ['true', '1']:
            active_var = 1
        elif request.GET.get("active").lower() in ['false', '0']:
            active_var = 0
        else:
            active_var = -1
    if active_var != -1:
        if "activity_type" in activity_params and "active" in activity_params:
            return_list = list(set(Activity.objects.filter(activity_type=request.GET.get("activity_type"), active=active_var).values_list('id', flat=True)))
        elif "active" in activity_params:
            return_list = list(set(Activity.objects.filter(active=active_var).values_list('id', flat=True)))
        elif "activity_type" in activity_params:
            return_list = list(set(Activity.objects.filter(activity_type=request.GET.get("activity_type")).values_list('id', flat=True)))
    else:
        #malformed request - "active" cannot be parsed
        return_list = None
    return return_list

def stringify_data_info(data_list_objects):
    data_id, device_id, activity_id, type_of_data, data_list, user_id, time_added = [], [], [], [], [], [], []
    for data in data_list_objects:
        data_id.append(data.id)
        device_id.append(data.device_id)
        activity_id.append(data.activity_id)
        type_of_data.append(data.type_of_data)
        data_list.append([json.loads(data.data)])
        user_id.append(data.user_id)
        time_added.append(data.time_added)

    data_objects = [{"data_id": daid, "device_id": did, "activity_id": aid, "type": tpe, "data": da, "user_id": uid, "time_added": tadd}
                        for daid, did, aid, tpe, da, uid, tadd in zip(data_id, device_id, activity_id, type_of_data, data_list, user_id, time_added)]
    return data_objects

@csrf_exempt
def dataout(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(['GET'])
    else:
        allowed_params = ["id", "user_id", "device_id", "activity_id", "type_of_data", "activity_type", "active", "repo", "commit", "device_name", "device_type", "before_time", "after_time"]
        errors  = validate_api_key(request, READ_PERMISSION())
        git_params = []
        device_params = []
        activity_params = []
        param_dictionary = {}
        time_before = None
        time_after = None
        for param in request.GET.dict():
            if param in allowed_params:
                if request.GET.get(param):
                    if param == "commit" or param == "repo":
                        git_params.append(param)
                    elif param == "device_name" or param == "device_type":
                        device_params.append(param)
                    elif param == "activity_type" or param == "active":
                        activity_params.append(param)
                    elif param == "before_time":
                        time_before = request.GET.get(param)
                    elif param == "after_time":
                        time_after = request.GET.get(param)
                    else:
                        if param == "id" or param == "user_id" or param == "device_id" or param == "activity_id":
                            try:
                                param_dictionary[param] = int(request.GET.get(param))
                            except:
                                #Value is malformed
                                errors.append(302)
                        else:
                            param_dictionary[param] = request.GET.get(param)
                else:
                    #param exists but has no value set
                    errors.append(302)
            else:
                #error, invalid get param
                errors.append(301)
        git_act_id = None
        if len(git_params) > 0:
            #get activity ids for the params and store in list, used to filter request later
            git_act_id = git_parser(git_params, request)
        device_dev_id = None
        if len(device_params) > 0:
            device_dev_id = device_parser(device_params, request)
        activity_act_id = None
        if len(activity_params) > 0:
            activity_act_id = activity_parser(activity_params, request)
            if not activity_act_id:
                #Malformed request - active cannot be parsed
                errors.append(302)
        if time_before:
            time_before = time_date_object(time_before)
            if not time_before:
                #Couldn't parse date/time string
                errors.append(302)
        if time_after:
            time_after = time_date_object(time_after)
            if not time_after:
                #Couldn't parse date/time string
                errors.append(302)

        data_json = []
        if len(errors) == 0:
            #Filter request
            data_list = Data.objects.filter(**param_dictionary)
            if git_act_id is not None:
                data_list = data_list.filter(activity_id__in=git_act_id)
            if device_dev_id is not None:
                data_list = data_list.filter(device_id__in=device_dev_id)
            if activity_act_id is not None:
                data_list = data_list.filter(activity_id__in=activity_act_id)
            if time_before:
                data_list = data_list.filter(time_added__lte=time_before)
            if time_after:
                data_list = data_list.filter(time_added__gte=time_after)
            data_json = stringify_data_info(data_list)
        #Response
        if len(errors) > 0:
            return JsonResponse({"success": False, "errors": errors, "data_objects": data_json}, status=statusCode(errors))
        else:
            return JsonResponse({"success": True, "errors": errors, "data_objects": data_json})
