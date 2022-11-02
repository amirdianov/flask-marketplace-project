from flask import Blueprint, request, flash, redirect, url_for, render_template, session
from werkzeug.security import generate_password_hash

from db_util import Database

admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static')
db = Database()


def login_admin():
    session['admin_logged'] = 1


def isLogged():
    return True if 'admin_logged' in session.keys() else False


def logout_admin():
    session.pop('admin_logged', None)


@admin.route('/')
def index():
    if not isLogged():
        return redirect(url_for('.login'))

    return redirect(url_for('.all_products_page'))


@admin.route('/login_admin', methods=['POST', 'GET'])
def login():
    if isLogged():
        return redirect(url_for('.index'))
    if request.method == 'POST':
        if db.getUsersCategory(request.form['email'], request.form['password']) == 1:
            login_admin()
            return redirect(url_for('.index'))
        else:
            flash('Неверные имя или пароль для админки')
    return render_template('admin/login_admin.html', title='Админ-панель')


@admin.route('/logout', methods=['POST', 'GET'])
def logout():
    if not isLogged():
        return redirect(url_for('.login'))
    logout_admin()
    return redirect(url_for('.login'))


@admin.route("/view_product/<int:product_id>", methods=["POST", "GET"])
def detail_product_page(product_id):
    product = db.getProductById(product_id)
    return render_template('view_product.html', product=product)


@admin.route("/all_products")
def all_products_page():
    cat = request.args.get('category')
    search = request.args.get('search')
    return render_template('admin/all_products.html', title='Все продукты', products=db.getProducts(cat, search))


@admin.route("/add_product", methods=["POST", "GET"])
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

    return render_template('admin/add_product.html', title="Добавление продукта")


@admin.route("/all_users")
def all_users_page():
    return render_template('admin/all_users.html', title='Все пользователи')


@admin.route("/add_user")
def add_user_page():
    return render_template('admin/add_user.html', title='Добавить пользователя')
