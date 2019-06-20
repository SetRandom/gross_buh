__author__ = "Denis Zhovner <hello@denizzo.ru>"
__version__ = '0.1'
from app import celery
from celery.schedules import crontab
from config import crontab_shedule
import modules.tasks

celery.conf.beat_schedule = {
    'rerun_check_': {
        'task': 'modules.tasks.rerun_check',
        'schedule': crontab(minute=f'{crontab_shedule}'),
    }
}
celery.conf.timezone = 'UTC'

if __name__ == '__main__':
    celery.start()
