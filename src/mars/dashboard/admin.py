from django.contrib import admin
from .models import Device
from .models import Api


admin.site.register(Device)
admin.site.register(Api)
