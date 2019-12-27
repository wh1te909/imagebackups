import subprocess

from django.db import models


class BackupJob(models.Model):
    name = models.CharField(max_length=255)
    status = models.CharField(default="n/a", max_length=255)
    started = models.DateTimeField(auto_now_add=True)
    model = models.CharField(default="n/a", max_length=255)
    serial = models.CharField(default="n/a", max_length=255)
    mounted = models.BooleanField(default=False)
    backup_size = models.CharField(default="n/a", max_length=30)
    celery_id = models.CharField(default="n/a", max_length=255)
    virus_scan_running = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class VirusScan(models.Model):
    backup = models.ForeignKey(BackupJob, related_name="backupjobs", on_delete=models.CASCADE)
    status = models.CharField(default="n/a", max_length=255)
    started = models.DateTimeField(auto_now_add=True)
    celery_id = models.CharField(default="n/a", max_length=255)

    def __str__(self):
        return self.backup.name
            
            
class BackgroundTask(models.Model):
    wipe_in_progress = models.BooleanField(default=False)

class DiskWipe(models.Model):
    status = models.CharField(default="n/a", max_length=255)
    celery_id = models.CharField(default="n/a", max_length=255)
    started = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.celery_id

class DiskClone(models.Model):
    status = models.CharField(default="n/a", max_length=255)
    celery_id = models.CharField(default="n/a", max_length=255)
    started = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.celery_id

class DiskCheck(models.Model):
    status = models.CharField(default="n/a", max_length=255)
    celery_id = models.CharField(default="n/a", max_length=255)
    started = models.DateTimeField(auto_now_add=True)
    model = models.CharField(default="n/a", max_length=255)
    serial = models.CharField(default="n/a", max_length=255)

    def __str__(self):
        return self.celery_id

