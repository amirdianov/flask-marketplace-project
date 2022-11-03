import os

from flask import Blueprint, request, flash, redirect, url_for, render_template, session
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from db_util import Database
from forms import AddEditProduct, LoginForm

admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static')
db = Database()
UPLOAD_FOLDER = '/static/media/'


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
    form = LoginForm()
    if isLogged():
        return redirect(url_for('.index'))
    if form.validate_on_submit():
        try:
            if db.getUsersCategory(request.form['email'], request.form['password']) == 1:
                login_admin()
                return redirect(url_for('.index'))
            else:
                flash('Неверные имя или пароль для админки', 'error')
        except:
            flash('Похоже нет Admin с введенными данными', 'error')
    return render_template('admin/login_admin.html', title='Админ-панель', form=form)


@admin.route('/logout', methods=['POST', 'GET'])
def logout():
    if not isLogged():
        return redirect(url_for('.login'))
    logout_admin()
    return redirect(url_for('.login'))


@admin.route("/view_product/<int:product_id>", methods=["POST", "GET"])
def detail_product_page(product_id):
    if not isLogged():
        return redirect(url_for('.login'))
    product = db.getProductById(product_id)
    return render_template('view_product.html', product=product)


@admin.route("/all_products", methods=["POST", "GET"])
def all_products_page():
    if not isLogged():
        return redirect(url_for('.login'))
    cat = request.args.get('category')
    search = request.args.get('search')
    if request.method == 'POST':
        if request.form.get('change'):
            pass
        elif request.form.get('delete'):
            db.deleteProductById(request.form['delete'])
    return render_template('admin/all_products.html', title='Все продукты', products=db.getProducts(cat, search))


@admin.route("/add_product", methods=["POST", "GET"])
def add_product_page():
    if not isLogged():
        return redirect(url_for('.login'))
    form = AddEditProduct()
    form.category.choices = [('0', 'Выберите категорию')]
    for g in db.getCategories():
        form.category.choices.append((g['id'], g['category_name']))
    if form.validate_on_submit():
        file = form.image.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, 'products/', filename))

        res = db.addProduct(form.product_name.data, form.price.data, form.text_info.data,
                            os.path.join(UPLOAD_FOLDER, 'products/', filename), form.category.data, form.count.data)
        if not res:
            flash("Ошибка добавления", "error")
        flash("Товар добавлен", "success")
        return redirect(url_for('.all_products_page'))

    return render_template('admin/add_product.html', title="Добавление продукта", form=form)


@admin.route("/all_users")
def all_users_page():
    if not isLogged():
        return redirect(url_for('.login'))
    return render_template('admin/all_users.html', title='Все пользователи')


@admin.route("/add_user")
def add_user_page():
    if not isLogged():
        return redirect(url_for('.login'))
    return render_template('admin/add_user.html', title='Добавить пользователя')
