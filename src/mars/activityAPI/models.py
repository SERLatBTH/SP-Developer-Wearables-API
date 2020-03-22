from django.db import models
from django.conf import settings

class Activity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    device_id = models.PositiveIntegerField()
    activity_type = models.CharField(max_length=50, default="standard")
    active = models.BooleanField(default=True)
    time_started = models.DateTimeField(auto_now=False, auto_now_add=True)
    time_ended = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)

class GitRepo(models.Model):
    name = models.TextField()
    activity = models.ForeignKey("Activity", on_delete=models.CASCADE)
    time_added = models.DateTimeField(auto_now=False, auto_now_add=True)

class GitCommit(models.Model):
    name = models.TextField()
    activity = models.ForeignKey("Activity", on_delete=models.CASCADE)
    time_added = models.DateTimeField(auto_now=False, auto_now_add=True)
