from django.conf import settings
from django.db import models


class Api(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=20, blank=False, null=False, unique=True)
    name = models.CharField(max_length=50)
    write_access = models.BooleanField(default=False)
    read_access = models.BooleanField(default=False)
    admin_access = models.BooleanField(default=False)
    time_added = models.DateTimeField(auto_now=False, auto_now_add=True)

    def __str__(self):
        return self.name


class Device(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    device_type = models.CharField(max_length=50)
    time_added = models.DateTimeField(auto_now=False, auto_now_add=True)
    def __str__(self):
        return self.name
    

