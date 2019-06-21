# checker_fns config
# Для регистрации нужно вызвать функцию registration из checker_fns.py

CHECKER_FNS_EMAIL = 'change@me.ru'
CHECKER_FNS_PHONE = '+70000000000'
CHECKER_FNS_NAME = 'Yolo'
CHECKER_FNS_PASSWD = ''

# Ссылка на бд где будем все хранить
database = 'postgresql://username:password@localhost:5432/database'

# порт на котором будет работать фласк
port = 8011
DEBUG = False

flask_secret_key = '' # любой набор букв не меньше 10 символов

# время жизни для проверки чека
lifetime_delta = 7

# пароль для дефолтного пользователя user
default_user_pwd = 'default_user_pwd'

## Celery
# время между ретраями
retry_delay = 30
# сколько раз ретраить задачу
max_retries = 5
# для выполнения переодических задач (в нотации cron)
crontab_shedule = '*/50'

# адрес до брокера
broker_url = 'amqp://user:password@localhost:5672/example_host'
