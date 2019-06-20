__author__ = "Denis Zhovner <hello@denizzo.ru>"
__version__ = '0.1'
from datetime import datetime


def add_log(logtext, component, level='INFO'):
    from modules.sql_model import Log
    _l = Log(date=datetime.now(), log=f'[{level}] [{component}] {logtext}')
    _l.save()


def validate_s(s):
    valide_keys = ['t', 's', 'fn', 'i', 'fp', 'n']
    try:
        d = {i.split('=')[0]: i.split('=')[1] for i in [j for j in s.split('&')]}
    except Exception as e:
        add_log(f'No valide string: {s} \n{e}', 'HELPER', 'WARN')
        return False
    if all([d.get(i) for i in valide_keys]):
        return True
    return False

def get_rubles(summ):
    return round(summ / 100, 2)

def create_qr_img(check):
    import qrcode
    img = qrcode.make()
    #todo