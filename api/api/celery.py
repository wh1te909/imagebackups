from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')

app = Celery('api', backend='redis://localhost', broker='redis://localhost')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.broker_url = 'redis://localhost:6379'
app.result_backend = 'redis://localhost:6379'
app.accept_content = ['application/json']
app.result_serializer = 'json'
app.task_serializer = 'json'
app.conf.task_track_started = True
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    from core.tasks import get_backup_size, check_wipe_task, check_backup_task, check_diskcheck_task, check_virus_task
    sender.add_periodic_task(45.0, get_backup_size.s(), name='get size')
    sender.add_periodic_task(15.0, check_wipe_task.s(), name='update wipe states')
    sender.add_periodic_task(20.0, check_backup_task.s(), name='update backup states')
    sender.add_periodic_task(25.0, check_diskcheck_task.s(), name='update diskcheck states')
    sender.add_periodic_task(30.0, check_virus_task.s(), name='update virus scan states')