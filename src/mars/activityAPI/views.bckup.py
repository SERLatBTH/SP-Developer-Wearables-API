from django.shortcuts import render

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework import status
from .serializers import ActivitySerializer
from .models import Activity

class ActivityList(APIView):
    def get(self,request):
        activityobjects = Activity.objects.all()
        serializer = ActivitySerializer(activityobjects, many=True)
        return Response(serializer.data)

    def post(self):
        pass
    
