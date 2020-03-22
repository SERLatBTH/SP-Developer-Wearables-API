from django.contrib import admin
from .models import Activity, GitRepo, GitCommit

admin.site.register(Activity)
admin.site.register(GitRepo)
admin.site.register(GitCommit)
