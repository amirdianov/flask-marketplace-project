from flask import Flask, render_template, request, url_for, redirect, make_response, session, flash
from db_util import Database, UserLogin
from forms import RegistrationForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, login_user, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'inform_project'
db = Database()
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"


# Гланвая страница доступна всем пользователям
@app.route('/')
def main_page_all():
    cat = request.args.get('category')
    search = request.args.get('search')
    params = {'products': db.getProducts(cat, search),
              'categories': db.getCategories(),
              'category_selected_id': int(cat) if cat else None,
              'search': search if search else ''}
    return render_template('main.html', **params)


# Страница регистрации, если пользователь успешно регистрируется,
# то перекидывает на авторизацию
@app.route('/registration', methods=['GET', 'POST'])
def registration_page():
    if current_user.is_authenticated:
        return redirect(url_for('profile_page'))
    if request.method == 'POST':
        session.pop('_flashes', None)
        if len(request.form['name']) > 1 and len(request.form['email']) > 4 and \
                request.form['psw'] == request.form['psw2']:
            hash = generate_password_hash(request.form['psw'])
            res = db.addUser(request.form['email'], hash)
            if res:
                flash("Вы успешно зарегистрированы", "success")
                return redirect(url_for('login_page'))
            else:
                flash("Ошибка при добавлении в БД", "error")
        else:
            flash("Неверно заполнены поля", "error")

    return render_template("registration.html", title="Регистрация")
    # form = RegistrationForm()
    # if form.validate_on_submit():
    #     return redirect(url_for('main_page_personal', username=request.form.get("email")))
    # return render_template('registration.html', title='Авторизация', form=form)


# Страница для авторизации
@app.route("/login", methods=["POST", "GET"])
def login_page():
    # заглушка, чтобы нельзя было перейти по данному адресу пользователю
    # который уже зарегистрирован
    if current_user.is_authenticated:
        return redirect(url_for('profile_page'))
    if request.method == "POST":
        user = db.getUserByEmail(request.form['email'])
        if user and check_password_hash(user['password'], request.form['psw']):
            userlogin = UserLogin().create(user)
            login_user(userlogin)
            return redirect(request.args.get("next") or url_for("profile_page"))

        flash("Неверная пара логин/пароль", "error")

    return render_template("login.html", title="Авторизация")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login_page'))


# Страница профиля зарегистрированного пользователя
@app.route('/profile')
@login_required
def profile_page():
    return render_template('profile.html')


@app.route("/add_product", methods=["POST", "GET"])
def add_product_page():
    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['post']) > 10:
            res = db.addProduct(request.form['name'], request.form['post'])
            if not res:
                flash('Ошибка добавления статьи 1', category='error')
            else:
                flash('Статья добавлена успешно', category='success')
        else:
            flash('Ошибка добавления статьи 2', category='error')

    return render_template('add_product.html', title="Добавление продукта")


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
