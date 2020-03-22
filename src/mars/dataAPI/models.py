from django.db import models
from django.conf import settings

class Data(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    device_id = models.PositiveIntegerField()
    activity_id = models.PositiveIntegerField()
    type_of_data = models.CharField(max_length=50)
    data = models.TextField()
    time_added = models.DateTimeField(auto_now=False, auto_now_add=True)
