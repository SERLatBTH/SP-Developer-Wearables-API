from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse, HttpRequest
from dashboard.models import Api, Device
from .models import Activity, GitRepo, GitCommit
import datetime
from django.views.decorators.csrf import csrf_exempt
import logging
import json

logger = logging.getLogger(__name__)

@csrf_exempt
def control(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    else:
        errors = []
        activity_id = 0
        activity_item = ""
        create_new_entry = False
        #header information
        user_id = int(request.headers.get('USER-ID'))
        api_key = request.headers.get('API-KEY')
        if user_id == "None" or api_key == "None":
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
                    #Active activity already exists
                    activity_item = Activity.objects.filter(user_id=user_id, active=True)[0]
                else:
                    #No active activity
                    create_new_entry = True
        
        #load json data
        data = json.loads(request.body)
        #Required json values
        device_id = data.get('device_id')
        action = data.get('action')    
        #Optional json values
        activity_type = data.get('type')
        repo = data.get('repo')
        commit = data.get('commit')
        if not activity_type:
            activity_type = "standard"
        if not device_id or not action:
            #malformed request error
            errors.append(302)
        if len(Device.objects.filter(id=device_id)) > 0:
            if Device.objects.filter(id=device_id)[0].user_id != user_id:
                #device_id doesn't match user_id
                errors.append(303)
        else:
            #device_id doesn't exist
            errors.append(304)    
        if len(errors) == 0:
            #Add/edit activity
            if create_new_entry and action == "start":
                #create new activity
                activity_item = Activity(device_id=device_id, activity_type=activity_type, user_id=user_id, active=True)
                activity_item.save()
                activity_id = activity_item.id
                if repo:
                    repo_item = GitRepo(name=repo, activity_id=activity_id)
                    repo_item.save()
                if commit:
                    commit_item = GitCommit(name=commit, activity_id=activity_id)
                    commit_item.save()
            elif create_new_entry and action == "stop":
                #No active activity to stop
                errors.append(200)
            elif action == "stop":
                #stop current activity
                activity_item.active = False
                activity_item.time_ended = datetime.datetime.now()
                activity_item.save()
                activity_id = activity_item.id
                if repo:
                    repo_item = GitRepo(name=repo, activity_id=activity_id)
                    repo_item.save()
                if commit:
                    commit_item = GitCommit(name=commit, activity_id=activity_id)
                    commit_item.save()
                activity_id = 0
            else:
                #update current activity with new info
                activity_id = activity_item.id
                if repo:
                    repo_item = GitRepo(name=repo, activity_id=activity_id)
                    repo_item.save()
                if commit:
                    commit_item = GitCommit(name=commit, activity_id=activity_id)
                    commit_item.save()
        #Response
        if len(errors) > 0:
            return JsonResponse({"success": False, "errors": errors, "activity_id": activity_id})
        else:
            return JsonResponse({"success": True, "errors": errors, "activity_id": activity_id})


@csrf_exempt
def status(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(['GET'])
    else:
        errors = []
        activity_id = 0
        #header information
        user_id = int(request.headers.get('USER-ID'))
        api_key = request.headers.get('API-KEY')
        if user_id == "None" or api_key == "None":
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
                    #Active activity already exists
                    activity_id = Activity.objects.filter(user_id=user_id, active=True)[0].id
                else:
                    #No active activity
                    activity_id = 0
        #Response
        if len(errors) > 0:
            return JsonResponse({"success": False, "errors": errors, "activity_id": activity_id})
        else:
            return JsonResponse({"success": True, "errors": errors, "activity_id": activity_id})


#100 = Invalid API key or user id
#101 = Invalid API permissions
#102 = Invalid API key (Global keys)
#200 = No activity available
#300 = General server error
#301 = Invalid variable used - one or more variables used not in database
#302 = malformed request
#303 = device doesnt belong to user
#304 = device_id doesn't exist