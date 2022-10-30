import os

from flask import Flask, render_template, request, url_for, redirect, make_response, session, flash
from db_util import Database, UserLogin
from forms import RegistrationForm, LoginForm, MakeOrder
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
MAX_CONTENT_LENGTH = 1024 * 1024
UPLOAD_FOLDER = 'static/media/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Для админ панели
app.register_blueprint(admin, url_prefix='/admin')


# Главная страница доступна всем пользователям
@app.route('/', methods=['GET', 'POST'])
def main_page_all():
    cat = request.args.get('category')
    search = request.args.get('search')
    params = {'products': db.getProducts(cat, search),
              'categories': db.getCategories(),
              'category_selected_id': int(cat) if cat else None,
              'search': search if search else ''}
    if request.method == 'POST':
        if not check_backet():
            make_products_backet()
        if check_count_product(request.form['backet_go']):
            add_product_backet(request.form['backet_go'])
    backet_flag = None
    if check_backet():
        if len(session['backet']):
            backet_flag = True
        else:
            backet_flag = False
    return render_template('main.html', **params, backet=backet_flag)


# Создает корзину, при добавлении первого товара
def make_products_backet():
    session['backet'] = []
    session.modified = True


# Проверяет, создана ли корзина
def check_backet():
    return True if 'backet' in session.keys() else False


# Проверяет можно ли добавить продукт по кнопке (в корзину с главной странцы)
def check_count_product(product_id):
    ans = db.getProductById(product_id)
    for product in session['backet']:
        if product['product_name'] == ans['product_name']:
            if product['count'] + 1 > ans['count_product']:
                flash('Больше таких товаров нет на складе', 'error')
                return False
            else:
                return True
    return True


# Добавляет продукт в корзину
def add_product_backet(product_id):
    ans = db.getProductById(product_id)
    flag = False
    for product in session['backet']:
        if product['product_name'] == ans['product_name']:
            product['count'] += 1
            flag = True
            session.modified = True
    if not flag:
        ans['count'] = 1
        session['backet'] += [ans]


# Удаляет корзину
def delete_backet():
    session.pop('backet', None)


# Увеличение количества продуктов +
def change_plus_backet(product_id):
    ans = db.getProductById(product_id)
    for product in session['backet']:
        if product['product_name'] == ans['product_name']:
            if product['count'] + 1 > ans['count_product']:
                flash('Больше таких товаров нет на складе', 'error')
            else:
                product['count'] += 1
                session.modified = True


# Уменьшение количества продуктов -
def change_minus_backet(product_id):
    ans = db.getProductById(product_id)
    for product in session['backet']:
        if product['product_name'] == ans['product_name']:
            product['count'] -= 1
            if product['count'] == 0:
                session['backet'].remove(product)
            session.modified = True
    if len(session['backet']) < 0:
        delete_backet()


# Удаление продукта из корзины
def delete_product_backet(product_id):
    ans = db.getProductById(product_id)
    for product in session['backet']:
        if product['product_name'] == ans['product_name']:
            session['backet'].remove(product)
            session.modified = True
            flash("Товар удален", "success")
    if len(session['backet']) < 0:
        delete_backet()


# Корзина
@app.route('/backet', methods=['GET', 'POST'])
@login_required
def backet():
    form = MakeOrder()
    if request.method == 'POST':
        if request.form.get('button_plus'):
            change_plus_backet(request.form.get('button_plus'))
        elif request.form.get('button_minus'):
            change_minus_backet(request.form.get('button_minus'))
        elif request.form.get('button_delete'):
            delete_product_backet(request.form.get('button_delete'))
        elif request.form.get('order'):
            db.makeOrder(current_user.get_id(), session['backet'], request.form.get('address'))
            delete_backet()
            flash('Заказ успешно создан', 'success')
            return redirect(url_for('main_page_all'))
    if len(session['backet']):
        backet_flag = True
    else:
        backet_flag = False
        flash("Корзина пуста", "error")
        return redirect(url_for('main_page_all'))
    return render_template('backet.html', products=session['backet'], form=form, backet=backet_flag)


# Страница регистрации, если пользователь успешно регистрируется,
# то перекидывает на авторизацию
@app.route('/registration', methods=['GET', 'POST'])
def registration_page():
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
            flash("Ошибка при добавлении в БД", "error")
    return render_template("registration.html", title="Регистрация", form=form)


# Страница для авторизации
@app.route("/login", methods=["POST", "GET"])
def login_page():
    # заглушка, чтобы нельзя было перейти по данному адресу пользователю
    # который уже зарегистрирован
    if current_user.is_authenticated:
        return redirect(url_for('profile_page'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.getUserByEmail(form.email.data)
        if user and check_password_hash(user['password'], form.password.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for("profile_page"))
        else:
            flash("Неверная пара логин/пароль", "error")
    return render_template("login.html", title="Авторизация", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    delete_backet()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login_page'))


@login_manager.user_loader
def load_user(user_id):
    print("load_user")
    return UserLogin().fromDB(user_id, db)


# Страница профиля зарегистрированного пользователя
@app.route('/profile')
@login_required
def profile_page():
    backet_flag = None
    if check_backet():
        if len(session['backet']):
            backet_flag = True
        else:
            backet_flag = False
    return render_template('profile.html', backet=backet_flag)


# Получает фото в формате png - толькоё
@app.route('/userava')
@login_required
def userava():
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
    product = db.getProductById(product_id)
    return render_template('view_product.html', product=product)


@app.errorhandler(404)
def pageNotFount(error):
    return render_template('page404.html', title="Страница не найдена")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
