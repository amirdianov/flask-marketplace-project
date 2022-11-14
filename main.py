import os
import time

from flask import Flask, render_template, request, url_for, redirect, make_response, session, flash
from db_util import Database, UserLogin
from forms import RegistrationForm, LoginForm, MakeOrder, ProfileForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from werkzeug.utils import secure_filename
from admin.admin import admin

app = Flask(__name__)
app.config['SECRET_KEY'] = 'inform_project'
db = Database()

# Для регистрации и авторизации пользователя
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"

# Для максимального объема хранения данных
MAX_CONTENT_LENGTH = 640 * 480
UPLOAD_FOLDER = 'static/media/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Для админ панели
app.register_blueprint(admin, url_prefix='/admin')


@app.route('/', methods=['GET', 'POST'])
def main_page_all():
    """Главная страница доступна всем пользователям"""
    # delete_session('saved')
    # make_session('saved', current_user_id=current_user.get_id())
    if request.method == 'POST':
        if request.form.get('backet_go'):
            if check_count_product(request.form['backet_go']):
                add_product_session('backet', request.form['backet_go'])
        elif request.form.get('saved_go'):
            add_product_session('saved', request.form['saved_go'])
    cat = request.args.get('category')
    search = request.args.get('search')
    users_products = {}
    if check_session('backet', current_user_id=current_user.get_id()):
        for element in session['backet'][current_user.get_id()]:
            users_products[element['id']] = element['count']
    users_saved_prodcuts = []
    if check_session('saved', current_user_id=current_user.get_id()):
        print(session['saved'][current_user.get_id()])
        for element in session['saved'][current_user.get_id()]:
            print(element)
            users_saved_prodcuts.append(element['id'])

    params = {'products': db.getProducts(cat, search),
              'categories': db.getCategories(),
              'category_selected_id': int(cat) if cat else None,
              'search': search if search else '',
              'users_products': users_products,
              'users_saved_prodcuts': users_saved_prodcuts,
              }
    print(users_saved_prodcuts)
    return render_template('main.html', title='Главная страница', **params)


@app.route('/ajax_button_backet', methods=['GET', 'POST'])
def ajax_button_backet():
    """ajax запрос для обработки добавления товара в корзину"""
    name = request.form['name']
    product_id = request.form['id']
    print('Сработал')
    # print(request.form['left'])
    if name == 'backet_go':
        add_product_session('backet', product_id)
        return {'make_two_buttons': True, 'id': product_id, 'left': db.getProductById(product_id)['count_product'] - 1}
    elif 'button_plus' in name:
        count = change_plus_backet(product_id)
        print({'make_two_buttons': False, 'id': product_id, 'count': count})
        return {'make_two_buttons': False, 'id': product_id, 'count': count,
                'left': db.getProductById(product_id)['count_product'] - count}
    elif 'button_minus' in name:
        count = change_minus_backet(product_id)
        print({'make_two_buttons': False, 'id': product_id, 'count': count})
        ans = db.getProductById(product_id)['count_product'] - count if count != False else \
            db.getProductById(product_id)['count_product']
        return {'make_two_buttons': False, 'id': product_id, 'count': count,
                'left': ans}


@app.route('/ajax_button_saved', methods=['GET', 'POST'])
def ajax_button_saved():
    """Метод для ajax запроса при нажатии на кнопки в корзину или в избранное"""
    name = request.form['name']
    product_id = request.form['id']

    saved_go = False
    saved_out = False
    if 'saved_go' in request.form['class'].split(' ')[-1]:
        add_product_session('saved', product_id)
        count = True
        saved_go = True
    elif 'saved_out' in request.form['class'].split(' ')[-1]:
        delete_product_session('saved', product_id, current_user.get_id())
        saved_out = True
    print('Отработал аякс запрос')
    return {'id': product_id, 'saved_go': saved_go, 'saved_out': saved_out}


@app.route('/ajax_button_in_backet', methods=['GET', 'POST'])
def ajax_button_in_backet():
    """Метод ajax для страницы корзины"""
    name = request.form['name']
    product_id = request.form['id']
    itog = 0
    if 'button_plus' in name:
        count = change_plus_backet(product_id)
        print(session['backet'][current_user.get_id()])

        for product in session['backet'][current_user.get_id()]:
            itog += db.getProductById(product['id'])['price'] * product['count']
        print(itog)
        return {'id': product_id, 'count': count,
                'left': db.getProductById(product_id)['count_product'] - count,
                'price': count * db.getProductById(product_id)['price'], 'itog': itog}
    elif 'button_minus' in name:
        count = change_minus_backet(product_id)
        print(session['backet'][current_user.get_id()])
        for product in session['backet'][current_user.get_id()]:
            itog += db.getProductById(product['id'])['price'] * product['count']
        ans = db.getProductById(product_id)['count_product'] - count if count != False else \
            db.getProductById(product_id)['count_product']
        print(itog)
        return {'id': product_id, 'count': count, 'left': ans,
                'price': count * db.getProductById(product_id)['price'], 'itog': itog}


@app.route('/ajax_button_in_saved', methods=['GET', 'POST'])
def ajax_button_in_saved():
    name = request.form['name']
    product_id = request.form['id']
    delete_product_session('saved', product_id, current_user_id=current_user.get_id())
    return {'ans': True}


def make_session(name, current_user_id=None):
    """Создает корзину (избранное), в момент первого входа пользователя на сайт"""
    session[name][current_user_id] = []
    session.modified = True


def check_session(name, current_user_id=None):
    """Проверяет, создана ли корзина (избранное) и не пустые ли они"""
    if name in session.keys():
        for user in session[name].keys():
            if user == current_user_id:
                if len(session[name][current_user_id]) != 0:
                    return True
                else:
                    return False
        else:
            return False
    else:
        session[name] = {}
        session.modified = True
        return False


def check_count_product(product_id):
    """Проверяет можно ли добавить продукт по кнопке (в корзину с главной странцы)"""
    ans = db.getProductById(product_id)
    for product in session['backet'][current_user.get_id()]:
        if product['id'] == ans['id']:
            if product['count'] + 1 > ans['count_product']:
                # flash('Больше таких товаров нет на складе', 'error')
                return False
            else:
                return True
    return True


def add_product_session(name, product_id):
    """Добавляет продукт в корзину"""
    ans = db.getProductById(product_id)
    flag = False
    if name == 'backet':
        for product in session['backet'][current_user.get_id()]:
            if product['id'] == ans['id']:
                product['count'] += 1
                flag = True
                session.modified = True
                return product['count']
        if not flag:
            ans = {'id': ans['id'], 'count': 1}
            # ans['count'] = 1
            session['backet'][current_user.get_id()] += [ans]
            session.modified = True
            return
    elif name == 'saved':
        for product in session['saved'][current_user.get_id()]:
            if product['id'] == ans['id']:
                return
        session['saved'][current_user.get_id()] += [{'id': ans['id']}]
        session.modified = True
    print(session['saved'][current_user.get_id()])
    print(len(session['saved'][current_user.get_id()]))


def delete_session(name):
    """Удаляет корзину или избранное"""
    session[name][current_user.get_id()] = []


def change_plus_backet(product_id):
    """Увеличение количества продуктов +"""
    ans = db.getProductById(product_id)
    for product in session['backet'][current_user.get_id()]:
        if product['id'] == ans['id']:
            if product['count'] + 1 > ans['count_product']:
                # flash('Больше таких товаров нет на складе', 'error')
                return product['count']
            else:
                product['count'] += 1
                session.modified = True
                return product['count']


def change_minus_backet(product_id):
    """Уменьшение количества продуктов -"""
    ans = db.getProductById(product_id)
    print('Минусую')
    for product in session['backet'][current_user.get_id()]:
        if product['id'] == ans['id']:
            product['count'] -= 1
            if product['count'] == 0:
                session['backet'][current_user.get_id()].remove(product)
                session.modified = True
                return False
            session.modified = True
            return product['count']


def delete_product_session(name, product_id, current_user_id=None):
    """# Удаление продукта из корзины (избранного)"""
    ans = db.getProductById(product_id)
    for product in session[name][current_user_id]:
        if product['id'] == ans['id']:
            session[name][current_user_id].remove(product)
            session.modified = True
            # flash("Товар удален", "success")


@app.route('/backet', methods=['GET', 'POST'])
@login_required
def backet():
    """Страница корзины"""
    form = MakeOrder()
    if request.method == 'POST':
        if request.form.get('button_plus'):
            change_plus_backet(request.form.get('button_plus'))
        elif request.form.get('button_minus'):
            change_minus_backet(request.form.get('button_minus'))
        elif request.form.get('button_delete'):
            delete_product_session('backet', request.form.get('button_delete'), current_user_id=current_user.get_id())
        elif request.form.get('order'):
            products = []
            for element in db.getProducts(None, None):
                for product in session['backet'][current_user.get_id()]:
                    if element['id'] == product['id']:
                        element['count'] = product['count']
                        products.append(element)
            db.makeOrder(current_user.get_id(), products, request.form.get('address'))
            delete_session('backet')
            flash('Заказ успешно создан', 'success')
            return redirect(url_for('main_page_all'))
    if check_session('backet', current_user_id=current_user.get_id()):
        if len(session['backet'][current_user.get_id()]):
            backet_flag = True
        else:
            backet_flag = False
            flash("Корзина пуста", "error")
            return redirect(url_for('main_page_all'))
    else:
        flash("Корзина пуста", "error")
        return redirect(url_for('main_page_all'))
    products = []
    for elem in db.getProducts(None, None):
        for product in session['backet'][current_user.get_id()]:
            if elem['id'] == product['id']:
                elem['count'] = product['count']
                products.append(elem)
    users_products = {}
    if check_session('backet', current_user_id=current_user.get_id()):
        for element in session['backet'][current_user.get_id()]:
            users_products[element['id']] = element['count']
    itog = 0
    for product in session['backet'][current_user.get_id()]:
        itog += db.getProductById(product['id'])['price'] * product['count']
    return render_template('backet.html', products=products, form=form,
                           backet=backet_flag, users_products=users_products, itog=itog)


@app.route("/saved", methods=["POST", "GET"])
@login_required
def saved_page():
    """Страница избранных"""
    if request.form.get('saved_out'):
        delete_product_session('saved', request.form['saved_out'], current_user_id=current_user.get_id())
    elif request.form.get('backet_go'):
        add_product_session('backet', request.form['backet_go'])

    if check_session('backet', current_user_id=current_user.get_id()):
        if len(session['backet']):
            backet_flag = True
        else:
            backet_flag = False
    else:
        backet_flag = False
    if check_session('saved', current_user_id=current_user.get_id()):
        if len(session['saved'][current_user.get_id()]):
            saved_flag = True
        else:
            saved_flag = False
            flash("Избранное пусто", "error")
            return redirect(url_for('main_page_all'))
    else:
        flash("Избранное пусто", "error")
        return redirect(url_for('main_page_all'))
    users_products = {}
    if check_session('backet', current_user_id=current_user.get_id()):
        for element in session['backet'][current_user.get_id()]:
            users_products[element['id']] = element['count']
    print(len(session['saved'][current_user.get_id()]))
    products = []
    for elem in db.getProducts(None, None):
        for product in session['saved'][current_user.get_id()]:
            if elem['id'] == product['id']:
                products.append(elem)
    return render_template('saved.html', products=products, backet=backet_flag,
                           users_products=users_products)


@app.route('/orders', methods=['GET', 'POST'])
@login_required
def orders_page():
    """Страница заказов внутри пользователя"""
    orders = db.getOrdersById(current_user.get_id())
    if orders:
        return render_template('orders.html', orders=orders)
    else:
        flash('У вас еще не было заказов', 'error')
        return redirect(url_for('main_page_all'))


@app.route('/orders/<int:num>', methods=['GET', 'POST'])
@login_required
def order_info_page(num):
    """Информация о заказе пользователя"""
    if db.getOrderByNumber(num):
        ans = db.getOrderByNumber(num)
        order_id = ans['id']
        products_info = db.getProductsIdByOrderId(order_id)
        products = []
        count_all_products = 0
        for element in products_info:
            count_all_products += element['count_product']
            product_special = db.getProductById(element['product_id'])
            product = {'product_name': product_special['product_name'], 'product_count': element['count_product'],
                       'summary': product_special['price'] * element['count_product'], 'id': element['product_id']}
            products.append(product)
        return render_template('view_order.html', products=products, summary_order=ans['sum_products'],
                               count_order=count_all_products)
    else:
        flash('Данного заказа не существует', 'error')
        return redirect(url_for('orders_page'))


# Страница регистрации, если пользователь успешно регистрируется,
# то перекидывает на авторизацию
@app.route('/registration', methods=['GET', 'POST'])
def registration_page():
    """Страница регистрации"""
    if current_user.is_authenticated:
        return redirect(url_for('profile_page'))
    form = RegistrationForm()
    if form.validate_on_submit():
        session.pop('_flashes', None)
        hash = generate_password_hash(form.password.data)
        res = db.addUser(form.email.data, hash)
        if res:
            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for('login_page'))
        else:
            flash("Ошибка, такой пользователь уже существует", "error")
    return render_template("registration.html", title="Регистрация", form=form)


@app.route("/login", methods=["POST", "GET"])
def login_page():
    """Страница для авторизации"""
    if current_user.is_authenticated:
        return redirect(url_for('profile_page'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.getUserByEmail(form.email.data)
        if user and check_password_hash(user['password'], form.password.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            if not check_session('saved', current_user_id=current_user.get_id()):
                make_session('saved', current_user_id=current_user.get_id())
            if not check_session('backet', current_user_id=current_user.get_id()):
                make_session('backet', current_user_id=current_user.get_id())
            flash(f'Вы вошли в аккаунт {form.email.data}', 'success')
            return redirect(request.args.get("next") or url_for("profile_page"))
        else:
            flash("Неверная пара логин/пароль", "error")
    return render_template("login.html", title="Авторизация", form=form)


@app.route('/logout')
@login_required
def logout():
    """Метод для удаления пользовтаеля из сессии"""
    delete_session('backet')

    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login_page'))


@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя в сессию"""
    print("load_user")
    return UserLogin().fromDB(user_id, db)


@app.route('/profile', methods=["POST", "GET"])
@login_required
def profile_page():
    """Страница профиля пользователя с картинкой и полями"""
    form = ProfileForm()
    if form.validate_on_submit():
        time.sleep(5)
        session.pop('_flashes', None)
        if form.password.data:
            hash = generate_password_hash(form.password.data)
            res = db.editUser(current_user.get_id(), form.email.data, hash)
        else:
            res = db.editUser(current_user.get_id(), form.email.data)

        if res:
            flash("Изменения сохранены", "success")
            return redirect(url_for('login_page'))
        else:
            flash("Ошибка при добавлении в БД", "error")
            return redirect(url_for('profile_page'))
    backet_flag = None
    if check_session('backet', current_user_id=current_user.get_id()):
        if len(session['backet']):
            backet_flag = True
        else:
            backet_flag = False
    context = db.getUser(current_user.get_id())
    context['password'] = ''
    return render_template('profile.html', backet=backet_flag, data=context, form=form)


@app.route('/userava')
@login_required
def userava():
    """Получение фото в профиле"""
    img = current_user.getAvatar(app)
    if not img:
        return ''
    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


# Метод для загрузки автара профиля
@app.route('/upload_avatar', methods=['POST', 'GET'])
@login_required
def upload_avatar():
    """Метод для загрузки фото профиля"""
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles/', filename))
            if db.deleteUserAvatar(current_user.get_id()):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles/',
                                       db.deleteUserAvatar(current_user.get_id())))
            res = db.updateUserAvatar(filename, current_user.get_id())
            if not res:
                flash("Ошибка обновления аватара", "error")
            flash("Аватар обновлен", "success")
        else:
            flash("Ошибка обновления аватара", "error")

    return redirect(url_for('profile_page'))


# Просмотр товара - вьюшка для товара
@app.route("/view_product/<int:product_id>", methods=["POST", "GET"])
def detail_product_page(product_id):
    """Детальный просмотр конкретного товара"""
    product = db.getProductById(product_id)
    if product:
        backet_flag = None
        if check_session('backet', current_user_id=current_user.get_id()):
            if len(session['backet']):
                backet_flag = True
            else:
                backet_flag = False
        return render_template('view_product.html', product=product, backet=backet_flag)
    else:
        flash('Такого товара не существует', 'error')
        return redirect(url_for('main_page_all'))


@app.errorhandler(404)
def pageNotFount(error):
    """Страница для страницы, которую не смогу найти браузер """
    return render_template('page404.html', title="Страница не найдена")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
