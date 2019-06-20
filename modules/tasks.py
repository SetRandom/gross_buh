__author__ = "Denis Zhovner <hello@denizzo.ru>"
__version__ = '0.1'

from app import celery
from modules.sql_model import CheckString
from datetime import datetime, timedelta
from config import retry_delay, max_retries, lifetime_delta
from modules.helper import add_log
from time import sleep


@celery.task(ignore_result=True)
def rerun_check():
    #todo написать sql запросом отсечение по дате
    # выбираем все чекстроки которые без ид чека и не с ошибкой
    all_no_check_id = CheckString.select().where(
        CheckString.check.is_null() & CheckString.error.is_null()
    ).order_by(CheckString.date.desc())
    if all_no_check_id.count():
        add_log(f'Start schedule task rerun_check. Count {all_no_check_id.count()}', 'TASK')
        for s in all_no_check_id:
            # если пришло время умирать, то умираем
            if s.date + timedelta(days=lifetime_delta) < datetime.now():
                add_log(f'Endlife task {s.date} {s.s}', "TASK")
                s.delete_instance()
                s.save()
                continue
            get_async_check.apply_async(args=[s.s])
            add_log(f'Run task {s.s}', "TASK")
            # sleep(10)
    return


@celery.task(bind=True,
             default_retry_delay=retry_delay,
             max_retries=max_retries,
             ignore_result=True)
def get_async_check(self, s):

    # fixme ? зачем это?
    if type(s) is list:
        s = s[0]

    q = CheckString.select().where(CheckString.s == s)
    if q.exists():
        check = CheckString.get(CheckString.s == s)
        if check.exists_check():
            return
        if check.error:
            return
    else:
        check = CheckString(s=s, date=datetime.now(), check=None)
        check.save()
    # return check.new_check().id
    try:
        check.new_check()
    except Exception as e:
        add_log(f'Exeption. {s} \n{e}', 'TASK', 'WARN')
        self.retry(exc=e)
    return
