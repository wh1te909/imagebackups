import subprocess
from time import sleep
from celery.result import AsyncResult

from api.celery import app

from .models import BackupJob, BackgroundTask, DiskWipe, DiskCheck, VirusScan, DiskClone

@app.task(bind=True)
def virus_scan_task(self, name, mounts, action):

    subprocess.run(["mkdir", f"/viruses/{name}"])

    if action == "move":
        cmd = ["clamscan", "-r", "-i", "-l", f"/clamlogs/{name}.log", f"--move=/viruses/{name}", f"/virusmount/{name}"]
    elif action == "copy":
        cmd = ["clamscan", "-r", "-i", "-l", f"/clamlogs/{name}.log", f"--copy=/viruses/{name}", f"/virusmount/{name}"]
    elif action == "delete":
        cmd = ["clamscan", "-r", "-i", "-l", f"/clamlogs/{name}.log", "--remove", f"/virusmount/{name}"]
    elif action == "nothing":
        cmd = ["clamscan", "-r", "-i", "-l", f"/clamlogs/{name}.log", f"/virusmount/{name}"]
    else:
        cmd = ["clamscan", "-r", "-i", "-l", f"/clamlogs/{name}.log", f"/virusmount/{name}"]
        
    r = subprocess.run(cmd)

    for i in mounts:
        subprocess.run(["umount", "-f", i])
        subprocess.run(["umount", "-l", i])
    
    subprocess.run(["losetup", "-D"])
    subprocess.run(["rm", "-rf", f"/virusmount/{name}"])
    
    backup = BackupJob.objects.get(name=name)
    backup.virus_scan_running = False
    
    backup.save(update_fields=["virus_scan_running"])
    backup2 = BackupJob.objects.get(name=name)

    return f"{name} virus scan finished with return code {r.returncode}"


@app.task(bind=True)
def disk_check_task(self):

    r = subprocess.Popen([
        "badblocks",
        "-v",
        "-s",
        "-o",
        f"/root/imagebackups/log/badblocks/{self.request.id}-bb.log",
        "/dev/cruH"
    ], stderr=subprocess.PIPE)

    log = f"/root/imagebackups/log/subprocess-logs/{self.request.id}-bb.log"

    while True:
        output = r.stderr.readline()
        if r.poll() is not None and output == b'':
            break
        if output:
            with open(log, 'a+') as f:
                f.write(output.decode())
    rc = r.poll()

    return f"{self.request.id} disk check job finished with return code {rc}"


@app.task(bind=True)
def backup_job_task(self, name):

    r = subprocess.Popen([
        "ddrescue", 
        "-d", 
        "-n", 
        "-r", 
        "0", 
        "-c", 
        "1Ki", 
        "/dev/cruH", 
        f"/tank/backups/{name}.img",
        f"/root/imagebackups/log/ddlogs/{name}.logfile"
    ], stdout=subprocess.PIPE)

    log = f"/root/imagebackups/log/subprocess-logs/{name}-subprocess.log"

    while True:
        output = r.stdout.readline()
        if r.poll() is not None and output == b'':
            break
        if output:
            with open(log, 'a+') as f:
                f.write(output.decode())
    rc = r.poll()

    return f"{name} backup job finished with return code {rc}"


@app.task()
def check_backup_task():
    backups = BackupJob.objects.all()
    for i in backups:
        if i.status != "SUCCESS":
            res = AsyncResult(i.celery_id)
            i.status = res.state
            i.save(update_fields=["status"])
    
    return "updated backup states"


@app.task()
def check_diskcheck_task():
    checks = DiskCheck.objects.all()
    for i in checks:
        if i.status != "SUCCESS":
            res = AsyncResult(i.celery_id)
            i.status = res.state
            i.save(update_fields=["status"])
    
    return "updated diskcheck states"



@app.task(bind=True)
def wipe_disk_task(self):

    r = subprocess.Popen([
        "ddrescue", 
        "--force", 
        "/dev/zero", 
        "/dev/cruH",
        f"/root/imagebackups/log/ddlogs/{self.request.id}-dd-wipe.log"
    ], stdout=subprocess.PIPE)

    log = f"/root/imagebackups/log/subprocess-logs/{self.request.id}-wipe.log"

    while True:
        output = r.stdout.readline()
        if r.poll() is not None and output == b'':
            break
        if output:
            with open(log, 'a+') as f:
                f.write(output.decode())
    rc = r.poll()

    return f"{self.request.id} wipe finished with return code {rc}"

@app.task(bind=True)
def clone_disk_task(self, pk):
    backup = BackupJob.objects.get(pk=pk)

    # clean the disk first
    subprocess.run(["wipefs", "-a", "/dev/cruH"])

    r = subprocess.Popen([
        "ddrescue", 
        "-f", 
        f"/tank/backups/{backup.name}.img", 
        "/dev/cruH",
        f"/root/imagebackups/log/clonelogs/{self.request.id}-dd-clone.log"
    ], stdout=subprocess.PIPE)

    log = f"/root/imagebackups/log/subprocess-logs/{self.request.id}-clone.log"

    while True:
        output = r.stdout.readline()
        if r.poll() is not None and output == b'':
            break
        if output:
            with open(log, 'a+') as f:
                f.write(output.decode())
    rc = r.poll()

    return f"{self.request.id} clone finished with return code {rc}"


@app.task()
def check_wipe_task():
    wipes = DiskWipe.objects.all()
    for i in wipes:
        if i.status != "SUCCESS":
            res = AsyncResult(i.celery_id)
            i.status = res.state
            i.save(update_fields=["status"])
    
    return "updated wipe states"

@app.task()
def check_clone_task():
    clones = DiskClone.objects.all()
    for i in clones:
        if i.status != "SUCCESS":
            res = AsyncResult(i.celery_id)
            i.status = res.state
            i.save(update_fields=["status"])
    
    return "updated clone states"

@app.task()
def check_virus_task():
    scans = VirusScan.objects.all()
    for i in scans:
        if i.status != "SUCCESS":
            res = AsyncResult(i.celery_id)
            i.status = res.state
            i.save(update_fields=["status"])
    
    return "updated virus scan states"

@app.task
def shutdown_server_task():
    sleep(5)
    subprocess.run(["shutdown", "-h", "now"])
    return "shutting down"


@app.task
def get_backup_size():
    backups = BackupJob.objects.all()
    for i in backups:
        if i.backup_size == "n/a" and i.status == "SUCCESS":
            p = subprocess.run(f"du -sh /tank/backups/{i.name}.img | cut -f1", shell=True, capture_output=True)
            size = p.stdout.decode().rstrip()
            i.backup_size = size
            i.save(update_fields=["backup_size"])
    
    return "updated backup sizes"

@app.task
def delete_backup_task(name):
    image = f"/tank/backups/{name}.img"
    subprocess.run(["rm", "-f", image])
    subprocess.run(["rm", "-f", f"/root/imagebackups/log/subprocess-logs/{name}-subprocess.log"])
    subprocess.run(["rm", "-f", f"/root/imagebackups/log/ddlogs/{name}.logfile"])
    return f"deleted {name}"
