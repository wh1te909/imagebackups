import subprocess
from time import sleep
import re
import psutil
import math
from loguru import logger
from celery.result import AsyncResult
import string

from django.conf import settings

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)

from rest_framework.response import Response
from rest_framework import status

from api.celery import app

from .models import BackupJob, BackgroundTask, DiskWipe, DiskCheck, VirusScan, DiskClone
from .serializers import BackupJobSerializer, DiskWipeSerializer, DiskCheckSerializer, VirusScanSerializer, DiskCloneSerializer
from .tasks import delete_backup_task, shutdown_server_task, wipe_disk_task, backup_job_task, disk_check_task, virus_scan_task, clone_disk_task
from .functions import get_hdd_info

logger.configure(**settings.LOG_CONFIG)

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

@api_view()
def server_info(request):
    tank_backup = psutil.disk_usage('/tank/backups')
    used = convert_size(tank_backup.used)
    free = convert_size(tank_backup.free)
    total = convert_size(tank_backup.total)
    
    return Response(
    {
        "used": used,
        "free": free,
        "total": total
    })


@api_view()
def shutdown_server(request):
    shutdown_server_task.delay()
    return Response("ok")

@api_view()
def cancel_virus_scan(request, pk):
    scan = VirusScan.objects.get(pk=pk)
    res = AsyncResult(scan.celery_id)
    if res.state == "STARTED":
        app.control.revoke(scan.celery_id, terminate=True, signal='SIGKILL')
        sleep(1)
        subprocess.run(["pkill", "-9", "clamscan"])
        sleep(1)

        m = subprocess.run(f"df -h | grep virusmount | grep {scan.backup.name} | sed -e 's/^.* //'", shell=True, capture_output=True)
        mounts = m.stdout.decode().rstrip().splitlines()

        for i in mounts:
            subprocess.run(["umount", "-f", i])
            subprocess.run(["umount", "-l", i])
        
        subprocess.run(["losetup", "-D"])
        subprocess.run(["rm", "-rf", f"/virusmount/{scan.backup.name}"])

        backup = BackupJob.objects.get(name=scan.backup.name)
        backup.virus_scan_running = False
        backup.save(update_fields=["virus_scan_running"])

        subprocess.run(["rm", "-f", f"/clamlogs/{scan.backup.name}.log"])
        scan.delete()

        return Response("ok")
    else:
        return Response(
            {"error": "Scan already finished. Wait a bit and refresh"},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view()
def cancel_backup(request, pk):
    backup = BackupJob.objects.get(pk=pk)

    app.control.revoke(backup.celery_id, terminate=True, signal='SIGKILL')
    sleep(1)

    delete_backup_task.delay(backup.name)
    backup.delete()
    return Response("ok")


@api_view(["POST"])
def rename_backup(request):

    pk = request.data["pk"]
    
    try:
        name = request.data["name"].replace(" ", "")
    except Exception:
        return Response(
            {"error": "Please enter a name"},
            status=status.HTTP_400_BAD_REQUEST
        )
    print(name)
    if not re.match('^[a-zA-Z0-9_-]+$', name):
        return Response(
            {"error": f"Only alphanumeric, underscores and dashes allowed"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if BackupJob.objects.filter(name=name).exists():
        return Response(
            {"error": f"{name} already exists. Please choose a different name"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    backup = BackupJob.objects.get(pk=pk)

    subprocess.run(["mv", f"/tank/backups/{backup.name}.img", f"/tank/backups/{name}.img"])
    subprocess.run(["mv", 
                    f"/root/imagebackups/log/subprocess-logs/{backup.name}-subprocess.log", 
                    f"/root/imagebackups/log/subprocess-logs/{name}-subprocess.log"])
    
    subprocess.run(["mv", 
                    f"/root/imagebackups/log/ddlogs/{backup.name}.logfile", 
                    f"/root/imagebackups/log/ddlogs/{name}.logfile"])

    backup.name = name
    backup.save(update_fields=["name"])

    return Response("ok")

    

@api_view(["DELETE"])
def delete_backup(request):
    backup = BackupJob.objects.get(pk=request.data["pk"])
    delete_backup_task.delay(backup.name)
    backup.delete()
    return Response("ok")


@api_view()
def cancel_wipe(request, celeryid):
    app.control.revoke(celeryid, terminate=True, signal='SIGKILL')
    sleep(1)
    return Response("ok")

@api_view()
def cancel_clone(request, celeryid):
    app.control.revoke(celeryid, terminate=True, signal='SIGKILL')
    sleep(1)
    return Response("ok")


@api_view()
def cancel_diskcheck(request, celeryid):
    app.control.revoke(celeryid, terminate=True, signal='SIGKILL')
    sleep(2)
    subprocess.run(["pkill", "-9", "badblocks"])
    sleep(1)
    subprocess.run(["rm", "-f", f"/root/imagebackups/log/subprocess-logs/{celeryid}-bb.log"])
    subprocess.run(["rm", "-f", f"/root/imagebackups/log/badblocks/{celeryid}-bb.log"])
    check = DiskCheck.objects.get(celery_id=celeryid)
    check.delete()
    return Response("ok")

@api_view()
def wipe_disk(request):

    if "STARTED" in BackupJob.objects.values_list('status', flat=True):
        return Response(
            {"error": "Cannot wipe. A backup is in progress"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if "STARTED" in DiskCheck.objects.values_list('status', flat=True):
        return Response(
            {"error": "Cannot wipe. A diskcheck is in progress"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    wipe = wipe_disk_task.delay()
    sleep(1)
    res = AsyncResult(wipe.task_id)
    DiskWipe(status=res.state, celery_id=wipe.task_id).save()
    return Response("ok")

@api_view()
def clone_disk(request, pk):

    if "STARTED" in BackupJob.objects.values_list('status', flat=True):
        return Response(
            {"error": "Cannot clone. A backup is in progress"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if "STARTED" in DiskCheck.objects.values_list('status', flat=True):
        return Response(
            {"error": "Cannot clone. A diskcheck is in progress"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if "STARTED" in DiskWipe.objects.values_list('status', flat=True):
        return Response(
            {"error": "Cannot clone. A wipe is in progress"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    clone = clone_disk_task.delay(pk)
    sleep(1)
    res = AsyncResult(clone.task_id)
    DiskClone(status=res.state, celery_id=clone.task_id).save()
    return Response("ok")

@api_view()
def get_wipes(request):
    wipes = DiskWipe.objects.all()
    return Response(DiskWipeSerializer(wipes, many=True).data)

@api_view()
def get_clones(request):
    clones = DiskClone.objects.all()
    return Response(DiskCloneSerializer(clones, many=True).data)


@api_view()
def get_bg_task(request):
    bg_task = BackgroundTask.objects.all().first()
    if bg_task.wipe_in_progress:
        return Response("yes")
    else:
        return Response("no")

@api_view()
def get_backups(request):
    backups = BackupJob.objects.all()
    return Response(BackupJobSerializer(backups, many=True).data)

@api_view()
def view_progress(request, pk):

    backup = BackupJob.objects.get(pk=pk)
    filename = f"/root/imagebackups/log/subprocess-logs/{backup.name}-subprocess.log"

    if backup.status == "SUCCESS":
        r = subprocess.run(["tail", "-7", filename], capture_output=True)
    else:
        r = subprocess.run(["tail", "-6", filename], capture_output=True)
    
    return Response(r.stdout.decode())

@api_view()
def view_diskcheck_progress(request, pk):
    check = DiskCheck.objects.get(pk=pk)
    filename = f"/root/imagebackups/log/subprocess-logs/{check.celery_id}-bb.log"
    r = subprocess.run(["less", "-F", filename], capture_output=True)

    printable = set(string.printable)
    out = "".join(filter(lambda x: x in printable, r.stdout.decode()))

    return Response(out.replace("test):", "test):\n").replace("errors)", "errors)\n"))

@api_view()
def view_virus_scan_progress(request, pk):

    scan = VirusScan.objects.get(pk=pk)
    filename = f"/clamlogs/{scan}.log"

    with open(filename, "r") as f:
        out = f.read()


    return Response(out)

@api_view()
def get_latest_wipe(request):
    try:
        wipe = DiskWipe.objects.latest("started")
    except Exception:
        return Response("none")

    return Response(wipe.celery_id)

@api_view()
def get_latest_clone(request):
    try:
        clone = DiskClone.objects.latest("started")
    except Exception:
        return Response("none")

    return Response(clone.celery_id)


@api_view()
def wipe_progress(request):

    wipe = DiskWipe.objects.latest("started")

    res = AsyncResult(wipe.celery_id)

    if res.state == "SUCCESS":
        return Response("wipefinished")

    filename = f"/root/imagebackups/log/subprocess-logs/{wipe.celery_id}-wipe.log"

    r = subprocess.run(["tail", "-6", filename], capture_output=True)
    out = r.stdout.decode()

    return Response(out)


@api_view()
def clone_progress(request):

    clone = DiskClone.objects.latest("started")

    res = AsyncResult(clone.celery_id)

    if res.state == "SUCCESS":
        return Response("clonefinished")

    filename = f"/root/imagebackups/log/subprocess-logs/{clone.celery_id}-clone.log"

    r = subprocess.run(["tail", "-6", filename], capture_output=True)
    out = r.stdout.decode()

    return Response(out)

@api_view()
def unmount_backup(request, pk):
    backup = BackupJob.objects.get(pk=pk)
    filename = f"/tank/backups/{backup.name}.img"
    subprocess.run(["umount", "-f", f"/mnt/{backup.name}"])
    subprocess.run(["umount", "-l", f"/mnt/{backup.name}"])
    backup.mounted = False
    backup.save()
    subprocess.run(["rm", "-rf", f"/mnt/{backup.name}"])
    return Response("ok")


@api_view()
def mount_by_offset(request, pk, offset):
    backup = BackupJob.objects.get(pk=pk)
    filename = f"/tank/backups/{backup.name}.img"
    subprocess.run(["mkdir", f"/mnt/{backup.name}"])
    rw = subprocess.run([
        "mount",
        "-t",
        "ntfs-3g",
        "-o",
        f"remove_hiberfile,rw,loop,offset={offset}",
        filename,
        f"/mnt/{backup.name}"
    ])
    if rw.returncode != 0:
        ro = subprocess.run([
            "mount",
            "-o",
            f"ro,loop,offset={offset}",
            filename,
            f"/mnt/{backup.name}"
        ])

    backup.mounted = True
    backup.save()
    return Response("ok")


@api_view()
def virus_scan(request, pk, action):
    backup = BackupJob.objects.get(pk=pk)
    filename = f"/tank/backups/{backup.name}.img"

    subprocess.run(["losetup", "/dev/loop99", "-P", filename])
    parts_cmd = f"ls -l /dev/loop99* | grep loop99p | wc -l"

    p = subprocess.run(parts_cmd, shell=True, capture_output=True)
    partitions = int(p.stdout.decode().rstrip())

    for i in range(1, partitions+1):
        subprocess.run(["mkdir", "-p", f"/virusmount/{backup.name}/{i}"])
        rw = subprocess.run([
            "mount",
            "-t",
            "ntfs-3g",
            "-o",
            f"remove_hiberfile,rw",
            f"/dev/loop99p{i}",
            f"/virusmount/{backup.name}/{i}"
        ])
        if rw.returncode != 0:
            ro = subprocess.run([
                "mount",
                "-o",
                "ro",
                f"/dev/loop99p{i}",
                f"/virusmount/{backup.name}/{i}"
            ])
    
    m = subprocess.run(f"df -h | grep {backup.name} | sed -e 's/^.* //'", shell=True, capture_output=True)
    mounts = m.stdout.decode().rstrip().splitlines()
    
    vscan = virus_scan_task.delay(name=backup.name, mounts=mounts, action=action)
    sleep(1)
    res = AsyncResult(vscan.task_id)

    VirusScan(backup=backup, status=res.state, celery_id=vscan.task_id).save()
    backup.virus_scan_running = True
    backup.save(update_fields=["virus_scan_running"])
    
    return Response("ok")


@api_view()
def mount_backup(request, pk):
    backup = BackupJob.objects.get(pk=pk)
    filename = f"/tank/backups/{backup.name}.img"

    lines_cmd = f"parted -s /tank/backups/{backup.name}.img unit b print | grep ntfs | wc -l"
    p1 = subprocess.run(lines_cmd, shell=True, capture_output=True)
    lines = int(p1.stdout.decode().rstrip())

    if not lines:
        return Response(
            {"error": "Something went wrong. Unable to mount"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    
    if lines == 1:
        offset_cmd = f"parted -s /tank/backups/{backup.name}.img unit b print | grep -i ntfs | tr -s ' ' | cut -d ' ' -f 3 | sed 's/[^0-9]*//g'"
        p = subprocess.run(offset_cmd, shell=True, capture_output=True)
        offset = p.stdout.decode().rstrip()
        subprocess.run(["mkdir", f"/mnt/{backup.name}"])
        rw = subprocess.run([
            "mount",
            "-t",
            "ntfs-3g",
            "-o",
            f"remove_hiberfile,rw,loop,offset={offset}",
            filename,
            f"/mnt/{backup.name}"
        ])

        if rw.returncode != 0:
            ro = subprocess.run([
                "mount",
                "-o",
                f"ro,loop,offset={offset}",
                filename,
                f"/mnt/{backup.name}"
            ])
            
        backup.mounted = True
        backup.save()
        return Response("oneparitiononly")
    else:
        offset_cmd = f"parted -s /tank/backups/{backup.name}.img unit b print | grep -i ntfs"
        p = subprocess.run(offset_cmd, shell=True, capture_output=True)
        paritions = p.stdout.decode().rstrip().splitlines()

        keys_cmd = f"parted -s /tank/backups/{backup.name}.img unit b print | grep -i ntfs | tr -s ' ' | cut -d ' ' -f 3 | sed 's/[^0-9]*//g'"
        p1 = subprocess.run(keys_cmd, shell=True, capture_output=True)
        keys = p1.stdout.decode().rstrip().splitlines()
        
        choices = {}
        for i, part in enumerate(paritions):
            choices[keys[i]] = paritions[i]

        return Response(choices)

@api_view()
def delete_virus_scan(request, pk):
    scan = VirusScan.objects.get(pk=pk)
    subprocess.run(["rm", "-f", f"/clamlogs/{scan.backup.name}.log"])
    scan.delete()
    return Response("ok")

@api_view()
@authentication_classes([])
@permission_classes([])
def get_disk_checks(request):
    checks = DiskCheck.objects.all()
    return Response(DiskCheckSerializer(checks, many=True).data)

@api_view()
@authentication_classes([])
@permission_classes([])
def get_virus_scans(request):
    scans = VirusScan.objects.all().select_related('backup')
    return Response(VirusScanSerializer(scans, many=True).data)  


@api_view(["POST"])
def create_backup(request):
    try:
        name = request.data["backupname"].replace(" ", "")
    except Exception:
        return Response(
            {"error": "Please enter a name"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not re.match('^[a-zA-Z0-9_-]+$', name):
        return Response(
            {"error": f"Only alphanumeric, underscores and dashes allowed"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if "STARTED" in BackupJob.objects.values_list('status', flat=True):
        return Response(
            {"error": "A backup job is already running"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if "STARTED" in DiskWipe.objects.values_list('status', flat=True):
        return Response(
            {"error": "A disk wipe is in progress. Please cancel that first"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if "STARTED" in DiskCheck.objects.values_list('status', flat=True):
        return Response(
            {"error": "A disk check is in progress. Please cancel that first"},
            status=status.HTTP_400_BAD_REQUEST
        )
    

    if BackupJob.objects.filter(name=name).exists():
        return Response(
            {"error": f"{name} already exists. Please choose a different name"},
            status=status.HTTP_400_BAD_REQUEST
        )

    info = get_hdd_info("/dev/cruH")

    backup = backup_job_task.delay(name)
    sleep(1)
    res = AsyncResult(backup.task_id)

    BackupJob(
        name=name, 
        status=res.state, 
        model=info["model"], 
        serial=info["serial"],
        celery_id=backup.task_id
    ).save()

    return Response("ok")

@api_view()
def start_disk_check(request):

    if "STARTED" in BackupJob.objects.values_list('status', flat=True):
        return Response(
            {"error": "Please wait for backup job to finish"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if "STARTED" in DiskWipe.objects.values_list('status', flat=True):
        return Response(
            {"error": "Please wait for disk wipe to finish"},
            status=status.HTTP_400_BAD_REQUEST
        )

    info = get_hdd_info("/dev/cruH")

    diskcheck = disk_check_task.delay()
    sleep(1)
    res = AsyncResult(diskcheck.task_id)

    DiskCheck(
        status=res.state, 
        model=info["model"], 
        serial=info["serial"],
        celery_id=diskcheck.task_id
    ).save()

    return Response("ok")


@api_view()
def get_disk(request):
    try:
        r = subprocess.run(["fdisk", "-l", "/dev/cruH"], capture_output=True)
        #r = subprocess.run("hdparm -I /dev/sda | sed -r '/^\s*$/d'", shell=True, capture_output=True)
        output = r.stdout.decode()
    except Exception as e:
        logger.warning(e)
        return Response("error")
    return Response(output)