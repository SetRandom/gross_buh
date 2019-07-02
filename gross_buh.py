__author__ = "Denis Zhovner <hello@denizzo.ru>"
__version__ = '0.1'

from flask import request, jsonify, render_template, abort, flash, redirect, url_for
from app import app
import config as cfg
from peewee import fn
from modules.helper import add_log, get_rubles, validate_s
from modules.sql_model import Check, Items, Log, Username, Product, CheckString
from flask_login import current_user, login_user, logout_user, login_required
from modules.tasks import get_async_check
from modules.forms import LoginForm
from werkzeug.urls import url_parse
from flask_paginate import Pagination, get_page_parameter

app.jinja_env.filters['rubles'] = get_rubles


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/')
def index():
    _ = Check.select().order_by(Check.summ.desc()).limit(1)
    try:
        big_check = _[0]
    except IndexError:
        big_check = False

    return render_template('index.html',
                           big_check=big_check,
                           )


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = Username.get(Username.login == form.username.data.strip())
            if user is None or not user.check_password(form.password.data):
                flash('Неверный пользователь или пароль')
                return redirect(url_for('login'))
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
    else:
        return render_template('login.html', title='Войти', form=form)


@app.route('/scan')
@login_required
def scan():
    return render_template('scan.html')


@app.route('/products')
@login_required
def products():
    search = False
    q = request.args.get('q')
    if q:
        search = True
        query = Product.select().where(Product.name ** f'%{q.strip()}%').order_by(Product.name)
    else:
        query = Product.select().order_by(Product.name)
    page = request.args.get(get_page_parameter(), type=int, default=1)


    pagination = Pagination(page=page, total=query.count(),
                            search=search,
                            record_name='query',
                            bs_version="4",
                            per_page=15)

    return render_template('product.html', query=query.paginate(page, 15), pagination=pagination)


@app.route('/prod/<int:prod_id>')
@login_required
def prod(prod_id):
    if not prod_id:
        return redirect(url_for('index'))
    item = Product.get_or_none(Product.id == prod_id)
    if not item:
        return redirect(url_for('index'))
    print(item)
    r = Items.select(Check).join(Check, on=(Items.check_id == Check.id)).where(Items.product_id == prod_id)

    return render_template('prod.html', query=r, i=item)


@app.route('/hands', methods=['GET', 'POST'])
@login_required
def hands():
    if request.method == 'POST':
        if not request.form:
            return abort(500)

        t1 = request.form.get('dateCheck', '').replace('-', '')
        t2 = request.form.get('timeCheck', '').replace(':', '')
        s = request.form.get('sumCheck', '').strip().replace(',', '.')
        fn = request.form.get('fnCheck', '').strip()
        i = request.form.get('fdCheck', '').strip()
        fp = request.form.get('fpCheck', '').strip()
        result_str = f't={t1}T{t2}00&s={s}&fn={fn}&i={i}&fp={fp}&n=1'
        print(result_str)
        if not validate_s(result_str):
            add_log(f"No valid request string {result_str}", "WEB", 'WARN')
            flash('Неверная строка чека!')
            return abort(500)

        add_log(f'Start job {result_str}', 'WEB')
        flash('Чек добавлен в обработку!')
        get_async_check.apply_async(args=[result_str])

    return render_template('hands.html')


@app.route('/check/<int:uid>')
def check(uid):
    if not uid:
        uid = 1

    if not Check.select().where(Check.id == uid):
        return abort(404)

    c = Check.get(Check.id == uid)
    items = Items.select().where(Items.check == c).order_by(Items.summ.desc())

    return render_template('check.html',
                           check=c,
                           items=items)


@app.route('/checks', methods=['GET'])
def checks():
    search = False
    q = request.args.get('q')
    if q:
        search = True
    page = request.args.get(get_page_parameter(), type=int, default=1)

    query = Check.select().order_by(Check.date_check.desc())

    pagination = Pagination(page=page, total=query.count(),
                            search=search,
                            record_name='query',
                            bs_version="4",
                            per_page=15)

    return render_template('checks.html',
                           query=query.paginate(page, 15),
                           pagination=pagination,
                           total=query.count())


@app.route('/checkstring', methods=['GET'])
@login_required
def checkstring():
    search = False
    q = request.args.get('q')
    if q:
        search = True
    page = request.args.get(get_page_parameter(), type=int, default=1)

    query = CheckString.select().where(CheckString.check.is_null()).order_by(CheckString.date.desc())

    pagination = Pagination(page=page, total=query.count(),
                            search=search,
                            record_name='query',
                            bs_version="4",
                            per_page=15)

    return render_template('checkstring.html',
                           query=query.paginate(page, 15),
                           pagination=pagination,
                           total=query.count())


@app.route('/summ')
def all_sum_check():
    all_sum = (Check.select(fn.SUM(Check.summ).alias('total'),
                            fn.date_trunc('month', Check.date_check).alias('month')).group_by(fn.alias('month')))
    return render_template('sum.html', query=all_sum)


@app.route('/log')
@login_required
def log():
    q = Log.select().order_by(Log.date.desc()).limit(200)
    return render_template('log.html', query=q)


# API

@app.route('/api/add_check', methods=['PUT'])
def api_add_check():
    # log.info(request.is_json)
    if not request.is_json:
        add_log(f"No valid request. Its no json", 'WEB', 'WARN')
        return jsonify(code=400, message="No valid request. Its no json"), 400

    js = request.get_json()
    s = js.get('string', '').strip()
    many_s = js.get('ManyString')

    # multiline send check
    if many_s:
        if type(many_s) is list:
            for item in many_s:
                if validate_s(item):
                    add_log(f'Start job {item}', 'WEB')
                    get_async_check.apply_async(args=[item])
            return jsonify(code=200, message=''), 200

    # default send check
    if s:
        if not validate_s(s):
            add_log(f"No valid request string {s}", "WEB", 'WARN')
            flash('Неверная строка чека!')
            return jsonify(code=400, message="No valid request"), 400

        add_log(f'Start job {s}', 'WEB')
        flash('Чек добавлен в обработку!')
        get_async_check.apply_async(args=[s])
        return jsonify(code=200, message=''), 200

    return jsonify(code=400, message="Invalid requests"), 400


@app.route('/api/list_check', methods=['GET'])
def api_list_check():
    data = []
    categories = []
    q = Check.select().order_by(Check.date_check)
    if not q.count():
        return jsonify(code=500, message="No data"), 500
    for i in q:
        categories.append(i.date_check.strftime("%d.%b"))
        data.append(get_rubles(i.summ))

    return jsonify({'series': [{'name': 'руб', 'data': data}],
                    'xaxis': {'categories': categories}}), 200


def main():
    from modules.sql_model import create_all, create_default_record
    create_all()
    create_default_record()
    add_log('Start APP', 'APP')
    app.run(host='0.0.0.0', port=cfg.port, debug=cfg.DEBUG,
            ssl_context=('cert.pem', 'key.pem'))


if __name__ == '__main__':
    # try:
    #     from db_migrate import migrate_me
    #     migrate_me()
    # except:
    #     print('No migrate')
    main()
