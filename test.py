if __name__ == '__main__':
    from datetime import datetime
    from time import sleep
    import modules.sql_model as sql
    from modules.helper import add_log
    import os
    from modules.tasks import get_async_check

    # os.remove('files/checker.db')
    sql.create_all()

    s = ['t=20190314T0013&s=299.00&fn=9289000100215013&i=65417&fp=1906984400&n=1',
         't=20190312T195800&s=1181.27&fn=8716000100001094&i=162049&fp=3896418463&n=1',
         't=20190302T1957&s=658.80&fn=9285000100066562&i=7042&fp=4031358114&n=1',
         't=20180920T2014&s=731.39&fn=8710000101882010&i=123346&fp=3085971920&n=1',
         't=20190316T2202&s=198.00&fn=9286000100262930&i=19056&fp=3258482418&n=1',
         't=20190316T214500&s=132.00&fn=8710000100723322&i=81751&fp=3797189661&n=1',
         't=20171019T1439&s=210.00&fn=8710000100526899&i=36503&fp=1979028934&n=1',
         't=20190314T214200&s=394.30&fn=8716000100001094&i=163416&fp=4109860984&n=1',
         't=20190325T200700&s=196.19&fn=8716000100001094&i=170196&fp=1990566828&n=1',
         't=20190323T220400&s=429.77&fn=8716000100020826&i=55423&fp=2271817126&n=1',
         't=20190320T2040&s=250.00&fn=9289000100215013&i=67956&fp=1699126328&n=1',
         't=20190320T192400&s=953.85&fn=8710000100514581&i=101565&fp=1257753946&n=1',
         ]
    for i in s:
        add_log(f'Start {i}', __name__)
        d = get_async_check.apply_async(args=[i])
        # while not d.ready():
        #     sleep(10)
        # c1 = sql.CheckString(s=i, date=datetime.now(), check=None)
        # c1.save()
        # try:
        #     c1.new_check()
        # except Exception as e:
        #     print(f'{e}')
        #     continue
