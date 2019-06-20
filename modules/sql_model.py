__author__ = "Denis Zhovner <hello@denizzo.ru>"
__version__ = '0.1'

from peewee import Model, TextField, DateTimeField, IntegerField, ForeignKeyField, FloatField, CharField, BooleanField
from datetime import datetime
from app import database, login
from flask_login import UserMixin
from config import DEBUG as debug


class ModelBase(Model):
    class Meta:
        database = database


# входящие чеки
class Check(ModelBase):
    # уникальный номер для чека
    # {ИНН}-{ФД}-{ФП}
    uid = TextField(unique=True)

    # дата в самом чеке
    date_check = DateTimeField()
    # дата приема в бд
    date = DateTimeField()

    # сумма в копейках
    summ = IntegerField(null=False)

    def __getattr__(self, item):
        if item == 'detail':
            return DetailCheck.get(DetailCheck.check == self)
        if item == 'count_item':
            return Items.select().where(Items.check == self).count()


# детали чеков
class DetailCheck(ModelBase):
    check = ForeignKeyField(Check)

    # aka fn
    fiscalDriveNumber = TextField()
    # адрес
    retailPlaceAddress = TextField(null=True)

    # nds18 -> nds20
    nds18 = IntegerField(null=True)
    nds10 = IntegerField(null=True)

    inn = TextField()

    operator = TextField(null=True)

    # fp
    fiscalSign = TextField()
    # fd
    fiscalDocumentNumber = TextField()
    # РН ККТ
    kktRegId = TextField(null=True)

    # dateTime = DateTimeField(null=True)


# товары
class Product(ModelBase):
    name = TextField()
    price = IntegerField()


# чек

class Items(ModelBase):
    check = ForeignKeyField(Check, unique=False)
    product = ForeignKeyField(Product, unique=False)
    # количество
    quantity = FloatField()
    summ = IntegerField(null=True)


# строки из чеков
class CheckString(ModelBase):
    s = TextField()
    date = DateTimeField()
    # ссылка на чек, необязательна если чек еще не сформировался
    check = ForeignKeyField(Check, null=True)
    # сообщение об ошибке создания чека
    error = TextField(null=True, default=None)

    # todo создаются одинаковые записи со строками, необходимо доработать
    # todo вынести функцию получения данных из фнс

    def new_check(self):
        import modules.checker_fns as fns

        if self.check:
            if debug:
                print('check exist')
            return self.check
        try:
            fns_detail, date_time = fns.get_list(self.s)
        except ValueError as e:
            self.error = f'{e}'
            self.save()
            return
        except Exception as e:
            raise Exception(f'Oh no! FNS error!\n {e}')
            # return None

        if not fns_detail:
            raise Exception('FNS not answer or answer empty')
            # return None

        inn = fns_detail.get('userInn', '')
        fiscalDocumentNumber = fns_detail.get('fiscalDocumentNumber', '')
        fiscalSign = fns_detail.get('fiscalSign', '')

        if not all([inn, fiscalDocumentNumber, fiscalSign]):
            raise Exception(f'requirements data empty!')
            # return None

        fiscalDriveNumber = fns_detail.get('fiscalDriveNumber', None)
        retailPlaceAddress = fns_detail.get('retailPlaceAddress', None)
        nds18 = fns_detail.get('nds18', None)
        nds10 = fns_detail.get('nds10', None)
        operator = fns_detail.get('operator', None)
        kktRegId = fns_detail.get('kktRegId', None)
        # date_time = fns_detail.get('date_time', None)
        totalSum = fns_detail.get('totalSum', None)

        # товары
        items = fns_detail.get('items', [])

        uid = f'{inn}-{fiscalDocumentNumber}-{fiscalSign}'

        select = Check.select().where(Check.uid == uid)
        if select.exists():
            if select.count() != 1:
                Exception(f'Error! Too many check! {uid}')
                # return None

            self.check = select.get()
            return self.check

        check = Check.create(uid=uid,
                             date_check=date_time,
                             date=datetime.now(),
                             summ=totalSum
                             )

        self.check = check

        detail_check = DetailCheck.create(check=check,
                                          fiscalDriveNumber=fiscalDriveNumber,
                                          retailPlaceAddress=retailPlaceAddress,
                                          nds18=nds18,
                                          nds10=nds10,
                                          inn=inn,
                                          operator=operator,
                                          fiscalSign=fiscalSign,
                                          fiscalDocumentNumber=fiscalDocumentNumber,
                                          kktRegId=kktRegId
                                          )
        check.save()
        detail_check.save()
        self.save()

        # items
        if len(items):
            for i in items:

                name = i.get('name', '').strip()
                quantity = i.get('quantity')
                price = i.get('price')
                summ = i.get('sum')
                if debug:
                    print('* '.join(map(str, [name,
                                              quantity,
                                              price,
                                              summ])))
                if not all([name, quantity, price]):
                    if debug:
                        print(f'requirements argument empty!')
                    continue
                if debug:
                    if i.get('properties'):
                        for j in i.get('properties'):
                            if debug:
                                print(f'properties {j}')
                    if i.get('modifiers'):
                        for j in i.get('modifiers'):
                            if debug:
                                print(f'modifiers {j}')

                item_product, create = Product.get_or_create(name=name,
                                                             price=int(price)
                                                             )
                if create:
                    if debug:
                        print('Create new product!')
                if not item_product:
                    if debug:
                        print(f'Oh no. Product not create! {name} {price}')
                    continue
                item_product.save()

                it = Items.create(check=self.check,
                                  product=item_product,
                                  quantity=float(quantity),
                                  summ=summ
                                  )
                it.save()

        return check

    def exists_check(self):
        if self.check:
            return True
        else:
            return False


# Для логирования
class Log(ModelBase):
    date = DateTimeField(default=datetime.now())
    log = TextField()


# лейблы для определения типов продуктов
# сам лейбл и ключевые слова
#
# class Label(ModelBase):
#     label = TextField()
#     tag = TextField()

# Пользователи
class Username(ModelBase, UserMixin):
    login = CharField(unique=True)
    p = CharField(max_length=100)
    name = CharField()
    disable = BooleanField(default=False)

    def set_password(self, password):
        import hashlib
        h = hashlib.sha256()
        h.update(password.encode('utf-8'))
        hashpass = h.hexdigest()[::3].upper()
        del (h)
        self.p = hashpass
        self.save()

    def check_password(self, password):
        import hashlib
        h = hashlib.sha256()
        h.update(password.encode('utf-8'))
        hashpass = h.hexdigest()[::3].upper()
        del h
        if self.p == hashpass:
            return True
        else:
            return False


@login.user_loader
def load_user(id):
    return Username.get_or_none(Username.id == int(id))


def create_all():
    database.create_tables([Check, DetailCheck,
                            CheckString, Items,
                            Log, Product, Username])


def create_default_record():
    from random import choices
    from string import ascii_letters, digits, punctuation
    from config import default_user_pwd

    if not Username.select().where(Username.login == 'user').exists():
        print('Create default user')
        user = Username.create(login='user', p='', name='User')
        if not default_user_pwd:
            password = ''.join(choices(ascii_letters + digits + punctuation, k=16))
        else:
            password = default_user_pwd
        print(f':::default user password - {password}')
        user.set_password(password)
        user.save()
