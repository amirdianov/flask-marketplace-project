import os

from flask import Flask, render_template, request, url_for, redirect, make_response, session, flash
from db_util import Database, UserLogin
from forms import RegistrationForm, LoginForm
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
        # delete_backet()
        add_product_backet(request.form['backet_go'])

    return render_template('main.html', **params)


def make_products_backet():
    session['backet'] = []


def check_product_in_backet():
    return True if 'backet' in session.keys() else False


def add_product_backet(product_id):
    session['backet'] += [{'product_id': product_id}]
    print(session['backet'])


def delete_backet():
    session.pop('backet', None)


@app.route('/backet', methods=['GET', 'POST'])
def backet():
    print(session['backet'])
    return render_template('backet.html', products=session['backet'])


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
            make_products_backet()
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


# Страница профиля зарегистрированного пользователя
@app.route('/profile')
@login_required
def profile_page():
    return render_template('profile.html')


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


@app.route("/view_product/<int:product_id>", methods=["POST", "GET"])
def detail_product_page(product_id):
    product = db.getProductById(product_id)
    return render_template('view_product.html', product=product)


@login_manager.user_loader
def load_user(user_id):
    print("load_user")
    return UserLogin().fromDB(user_id, db)


@app.errorhandler(404)
def pageNotFount(error):
    return render_template('page404.html', title="Страница не найдена")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
