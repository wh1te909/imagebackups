from django.contrib import admin
from .models import BackupJob, BackgroundTask, DiskWipe, DiskCheck, VirusScan, DiskClone

admin.site.register(BackupJob)
admin.site.register(BackgroundTask)
admin.site.register(DiskWipe)
admin.site.register(DiskCheck)
admin.site.register(VirusScan)
admin.site.register(DiskClone)