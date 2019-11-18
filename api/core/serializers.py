from rest_framework import serializers

from .models import BackupJob, DiskWipe, DiskCheck, VirusScan

class BackupJobSerializer(serializers.ModelSerializer):

    class Meta:
        model = BackupJob
        fields = "__all__"


class DiskWipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = DiskWipe
        fields = "__all__"


class DiskCheckSerializer(serializers.ModelSerializer):

    class Meta:
        model = DiskCheck
        fields = "__all__"

class VirusScanSerializer(serializers.ModelSerializer):
    backup_name = serializers.ReadOnlyField(source='backup.name')

    class Meta:
        model = VirusScan
        fields = ("id", "status", "started", "celery_id", "backup", "backup_name",)