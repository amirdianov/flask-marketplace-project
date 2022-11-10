import os

from flask import Blueprint, request, flash, redirect, url_for, render_template, session, make_response
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from db_util import Database
from forms import AddEditProduct, LoginForm

admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static')
db = Database()
UPLOAD_FOLDER = '/static/media/'

IMG = 'C:/Users/amird/PycharmProjects/flask-marketplace-project'


def login_admin(id):
    session['admin_logged'] = id


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
                login_admin(db.getUserByEmail(request.form['email'])['id'])
                flash(f'Вы вошли в админ-панель', 'success')

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
    flash('Вы вышли из админ панели', 'success')
    return redirect(url_for('.login'))


@admin.route("/view_product/<int:product_id>", methods=["POST", "GET"])
def detail_product_page(product_id):
    if not isLogged():
        return redirect(url_for('.login'))
    if db.getProductById(product_id):
        product = db.getProductById(product_id)

        return render_template('admin/view_product_admin.html', product=product)
    flash('Такого товара не существует', 'error')
    return redirect(url_for('.all_products_page'))


@admin.route('/productphoto/<int:product_id>')
def product_photo(product_id):
    img = db.getPhoto(product_id)
    if not img:
        return ''
    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


@admin.route("/all_products", methods=["POST", "GET"])
def all_products_page():
    if not isLogged():
        return redirect(url_for('.login'))
    cat = request.args.get('category')
    search = request.args.get('search')
    if request.method == 'POST':
        if request.form.get('change'):
            product = db.getProductById(request.form['change'])
            form = AddEditProduct()
            form.category.choices = []
            for g in db.getCategories():
                form.category.choices.append((g['id'], g['category_name']))
            form.category.default = product['category']
            form.process()
            form.count.data = product['count_product']
            form.product_name.data = product['product_name']
            form.price.data = product['price']
            form.text_info.data = product['text_info']
            return render_template('admin/add_edit_product.html', title='Редактирование', form=form,
                                   product_id=request.form['change'])
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
        if not request.form.get('change'):
            file = form.image.data
            filename = secure_filename(file.filename)

            res = db.add_edit_Product('add', form.product_name.data, form.price.data, form.text_info.data,
                                      os.path.join(UPLOAD_FOLDER, 'products/', filename), form.category.data,
                                      form.count.data)
            if res:
                flash("Товар добавлен", "success")
                file.save(os.path.join(IMG + UPLOAD_FOLDER, 'products/', filename))

            flash("Ошибка добавления", "error")

            return redirect(url_for('.all_products_page'))
        elif request.form.get('change'):
            file = form.image.data
            filename = secure_filename(file.filename)
            if filename:
                os.remove(IMG + db.deleteProductPhoto(request.form['change']))
                file.save(os.path.join(IMG + UPLOAD_FOLDER, 'products/', filename))
            else:
                filename = db.getProductById(request.form['change'])['image_path']
            res = db.add_edit_Product('change', form.product_name.data, form.price.data,
                                      form.text_info.data,
                                      os.path.join(UPLOAD_FOLDER, 'products/', filename), form.category.data,
                                      form.count.data, request.form['change'])
            if not res:
                flash("Ошибка добавления", "error")
            flash("Товар изменен", "success")
            return redirect(url_for('.all_products_page'))

    return render_template('admin/add_edit_product.html', title="Добавление продукта", form=form)


@admin.route("/all_users", methods=['POST', 'GET'])
def all_users_page():
    print('Я тут')
    if not isLogged():
        return redirect(url_for('.login'))
    if request.method == 'POST':
        print('Пост запрос получил')
        id_user_to_change = request.form.get('change_category')
        user = db.getUser(id_user_to_change)
        if user['category'] == 1:
            new_category = 2
        else:
            new_category = 1
        print(id_user_to_change, new_category)
        db.changeUserCategory(id_user_to_change, new_category)
    users = db.getUsers()
    categories = db.getCategories()

    for user in users:
        if user['category'] == 1:
            user['category'] = 'admin'
        elif user['category'] == 2:
            user['category'] = 'user'
    return render_template('admin/all_users.html', title='Все пользователи', users=users, categories=categories,
                           current_user_id=session['admin_logged'])
