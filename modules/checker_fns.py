# https://majordomo.smartliving.ru/forum/viewtopic.php?t=3933
# https://habr.com/post/358966/

__author__ = "Denis Zhovner <hello@denizzo.ru>"
__version__ = '0.3'
import requests
from requests.auth import HTTPBasicAuth
from time import sleep
from ..config import CHECKER_FNS_EMAIL as EMAIL
from ..config import CHECKER_FNS_PHONE as PHONE
from ..config import CHECKER_FNS_NAME as NAME
from ..config import CHECKER_FNS_PASSWD as PASSWD

API_URL = 'https://proverkacheka.nalog.ru:9999'
REG_URL = API_URL + '/v1/mobile/users/signup'
AUTH_URL = API_URL + '/v1/mobile/users/login'


def registration(email=EMAIL, name=NAME, phone=PHONE):
    '''
    Регистрация на сайте proverkacheka.nalog.ru
    Пароль должны прислать на телефон
    :param email: действующий эмайл
    :param name: имя (латиницей)
    :param phone: телефон в формате +79000000000
    :return: Истина - зарегестрировались
    '''
    j = {"email": email,
         "name": name,
         "phone": phone}
    r = requests.post(REG_URL, json=j)
    if r.status_code == requests.codes.ok:
        return True
    else:
        return False


def login(phone, password):
    r = requests.get(AUTH_URL, auth=HTTPBasicAuth(phone, password))


def generate_check(qrstring):
    """
    Разбираем из qr строки значения и формируем ссылки
    :param qrstring: qr строка
    :return: ссылка для получения чека, ссылка для проверки чека, дата чека
    """
    from datetime import datetime
    # разбираем строку на словарь
    d = {i.split('=')[0]: i.split('=')[1] for i in [i for i in qrstring.split('&')]}

    fn = d.get('fn')
    fd = d.get('i')
    fp = d.get('fp')
    s = d.get('s').replace('.', '')
    # print(d.get('t'))
    date = datetime.strptime(d.get('t')[:13], '%Y%m%dT%H%M')
    url = f'{API_URL}/v1/inns/*/kkts/*/fss/{fn}/tickets/{fd}?fiscalSign={fp}&sendToEmail=no'
    url_check = f'{API_URL}/v1/ofds/*/inns/*/fss/{fn}/operations/1/tickets/{fd}?fiscalSign={fp}&date={date.isoformat()}&sum={s}'
    return url, url_check, date


def get_list(qrstring, phone=PHONE, password=PASSWD):
    url, url_check, date = generate_check(qrstring)
    # сначала проверяем чек
    # print(f'Url check {url_check} ...')
    r = requests.get(url_check,
                     headers={'device-id': '', 'device-os': ''},
                     auth=HTTPBasicAuth(phone, password))
    # print(f'Url check return {r.status_code}')
    if r.status_code == 204 or r.status_code == 200:
        # если все ок то ждем 10 сек и получаем инфу,
        # если инфы не было, то делаем еще 3 попытки
        for i in range(3):
            sleep(10)
            # print(f'Get check')
            r = requests.get(url,
                             headers={'device-id': '', 'device-os': ''},
                             auth=HTTPBasicAuth(phone, password))
            # print(f'Get check return {r.status_code}')
            # print(f'Content len {len(r.content)}')
            if not r.status_code == requests.codes.ok:
                raise r.raise_for_status()
            if not r.content.strip():
                continue
            items = r.json().get('document').get('receipt')
            return items, date
    elif r.status_code == 406:
        raise ValueError('406')

    raise Exception('Null')


if __name__ == '__main__':
    q = 't=20190302T1957&s=658.80&fn=9285000100066562&i=7042&fp=4031358114&n=1'
    l = get_list(q, PHONE, PASSWD)
    print(l)
