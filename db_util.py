import datetime
import math
import os
import random
import time

import psycopg2
from flask import url_for
from psycopg2 import OperationalError

from flask_login import UserMixin
from werkzeug.security import check_password_hash


class UserLogin(UserMixin):
    """Класс, созданный для работы с конкртеным пользователем, авторизованным на сайте"""

    def fromDB(self, user_id, db):
        """Загрузка пользователя"""
        self.__user = db.getUser(user_id)
        return self

    def create(self, user):
        """Создание юзера для его логина"""
        self.__user = user
        return self

    def get_id(self):
        """Получение id текущего пользователя"""
        return str(self.__user['id'])

    def get_category(self):
        """Поулчение категории текущего пользователя"""
        return str(self.__user['category'])

    def getAvatar(self, app):
        """Получение аватара текущего пользователя"""
        img = None
        if not self.__user['profile']:
            with app.open_resource(app.root_path + url_for('static', filename='media/profiles/default_avatar.png'),
                                   'rb') as f:
                img = f.read()
                # print(img)
        else:
            img = self.__user['profile']
            with app.open_resource(app.root_path + url_for('static', filename=f'media/profiles/{img}'),
                                   'rb') as f:
                img = f.read()
        return img

    def verifyExt(self, filename):
        """Проверка на то, что загруженная фотография была PNG формата"""
        ext = filename.rsplit('.', 1)[1]
        if ext == "png" or ext == "PNG":
            return True
        return False


class Database:
    """Класс для установления подключения к БД"""

    def __init__(self):
        self.con = psycopg2.connect(
            dbname="marketplace_db",
            user="postgres",
            password="Amir2003",
            host="localhost",
            port=5432
        )
        self.cur = self.con.cursor()

    # todo %s
    def getProducts(self, cat, search):
        """Выведение всех продуктов по определенынм критериям"""
        if cat and search:
            query = f"SELECT * FROM products where " \
                    f"category= {cat} and count_product > 0 and " \
                    f"(product_name LIKE '%{search}%' or " \
                    f"text_info LIKE '%{search}%') order by id asc "
            self.cur.execute(query)

        elif cat:
            query = 'SELECT * FROM products where ' \
                    'category= %s and count_product > 0 order by id asc', (cat,)
            self.cur.execute(*query)

        elif search:
            query = f"SELECT * FROM products where count_product > 0  and " \
                    f"(product_name LIKE '%{search}%' or text_info LIKE '%{search}%') order by id asc"
            self.cur.execute(query)

        else:
            query = f"SELECT * FROM products where count_product > 0 order by id asc"
            self.cur.execute(query)

        res = self.prepare_data(self.cur.fetchall())
        if res:
            return res
        return []

    def getProductById(self, product_id):
        """Получение продукта по ID"""
        # print(product_id)
        query = f'SELECT * FROM products where id= {product_id}'
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())
        if res:
            return res[0]
        return False

    def getCategories(self):
        """Получение категорий для селектора - фильтрация продуктов"""
        query = f'SELECT * FROM products_categories order by category_name'
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())
        if res:
            return res
        else:
            return []

    def getPhoto(self, product_id):
        """Получение фото продукта для редактирования объявления"""
        query = 'SELECT * FROM products where id=%s', (product_id,)
        self.cur.execute(*query)
        res = self.prepare_data(self.cur.fetchall())[0]
        img = r'C:\Users\amird\PycharmProjects\flask-marketplace-project' + res['image_path']
        with open(img, 'rb') as f:
            img = f.read()
        return img

    # todo %s
    def add_edit_Product(self, type_operation, product_name, price, text_info, image_path, category, count_product,
                         product_id=None):
        """Добавление, изменение продуктов"""
        if type_operation == 'add':
            try:
                query = 'INSERT INTO products (product_name, price, text_info, image_path, category, count_product)' \
                        'VALUES (%s,%s,%s,%s,%s,%s)', (product_name, price, text_info, image_path, category, count_product)
                self.cur.execute(*query)
                self.con.commit()
                return True
            except:
                return False
        else:
            try:
                query = f"UPDATE products SET product_name = '{product_name}' where id = {product_id};" \
                        f"UPDATE products SET price = '{price}' where id = {product_id};" \
                        f"UPDATE products SET text_info = '{text_info}' where id = {product_id};" \
                        f"UPDATE products SET image_path = '{image_path}' where id = {product_id};" \
                        f"UPDATE products SET category = '{category}' where id = {product_id};" \
                        f"UPDATE products SET count_product = '{count_product}' where id = {product_id};"
                self.cur.execute(query)
                self.con.commit()
                return True
            except:
                return False

    def deleteProductById(self, product_id):
        """Удаление продукта, в случае нехватки его на складе"""
        query = 'UPDATE products SET count_product = 0 where id = %s', (product_id,)
        self.cur.execute(*query)
        self.con.commit()
        return True

    def deleteProductPhoto(self, get_id):
        """Удаление фото продукта"""
        query = 'SELECT image_path FROM products WHERE id = %s', (get_id,)
        self.cur.execute(*query)
        filename = self.prepare_data(self.cur.fetchall())[0]
        if filename['image_path']:
            return filename['image_path']

    def getUser(self, user_id):
        """Получение информации о пользователе по id"""
        query = "SELECT * FROM users WHERE id = %s", (user_id,)
        self.cur.execute(*query)
        res = self.prepare_data(self.cur.fetchall())[0]
        if not res:
            print('Нет такого')
            return False
        return res

    def getUsers(self):
        """Список всех пользователей """
        query = f"SELECT * FROM users order by id DESC"
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())
        if not res:
            print('Нет такого')
            return False
        return res

    def getUserByEmail(self, email):
        """Получение информации о пользователе по email"""
        query = 'SELECT * FROM users WHERE email = %s', (email,)
        self.cur.execute(*query)

        res = self.prepare_data(self.cur.fetchall())[0]
        if not res:
            print('Нет такого')
            return False
        return res

    def getUsersCategory(self, email, password):
        """Получение категории пользователя, для доступа к админке исключительно АДМИНАМ"""
        query = 'SELECT * FROM users WHERE email = %s', (email,)
        self.cur.execute(*query)
        res = self.prepare_data(self.cur.fetchall())[0]
        # print(res)
        pas = res['password']
        if not res:
            print('Нет такого')
            return False
        # print(pas)
        if check_password_hash(pas, password):
            print('СОШЛОСЬ')
            return res['category']

    def addUser(self, email, psw):
        """Регистрация пользователя, внесение в бд"""
        query = 'SELECT COUNT(*) as count FROM users WHERE email LIKE %s', (email,)
        self.cur.execute(*query)
        res = self.prepare_data(self.cur.fetchall())
        # print(res)
        if res[0]['count'] > 0:
            print("Пользователь с таким email уже существует")
            return False

        query = 'INSERT INTO users (email, password) VALUES (%s, %s)', (email, psw)
        self.cur.execute(*query)
        self.con.commit()
        return True

    # todo %s
    def editUser(self, user_id, email, psw=None):
        """Изменение данных о пользователе: пароль, почта"""
        try:
            query = f"UPDATE users SET email = '{email}' where id = '{user_id}';"
            self.cur.execute(query)
            self.con.commit()
            if psw:
                try:
                    query = f"UPDATE users SET password = '{psw}' where id = '{user_id}';"
                    self.cur.execute(query)
                    self.con.commit()
                except:
                    return False

            return True
        except:
            return False

    def updateUserAvatar(self, avatar, user_id):
        """Изменение аватарки профиля"""
        if not avatar:
            return False
        query = 'UPDATE users SET profile = %s where id = %s', (avatar, user_id)
        self.cur.execute(*query)
        self.con.commit()
        return True

    def deleteUserAvatar(self, get_id):
        """Удаление аватара профиля"""
        query = 'SELECT profile FROM users where id = %s', (get_id,)
        self.cur.execute(*query)
        filename = self.prepare_data(self.cur.fetchall())[0]
        if filename['profile']:
            return filename['profile']

    def changeUserCategory(self, id_user_to_change, new_category):
        """Изменение категории пользователя"""
        query = 'UPDATE users SET category = %s where id=%s', (new_category, id_user_to_change)
        self.cur.execute(*query)
        self.con.commit()

    def makeOrder(self, user_id, products, address):
        """Создание заказа"""
        now = datetime.datetime.now()
        id_products = []
        sum_products = 0
        number = random.randint(10000, 99999)
        for product in products:
            id_products.append(product['id'])
            sum_products = sum_products + product['count'] * product['price']
        query = f"INSERT INTO orders (user_id, sum_products, time_now, address, number_order) " \
                'VALUES (%s,%s,%s,%s,%s)', (user_id, sum_products, now, address, number)
        self.cur.execute(*query)
        self.con.commit()
        query_again = 'SELECT id FROM orders WHERE number_order = %s', (number,)
        self.cur.execute(*query_again)
        order_id = self.prepare_data(self.cur.fetchall())[0]['id']
        # print(order_id)
        for product in products:
            query = 'INSERT INTO products_ordered (order_id, product_id, count_product)' \
                    'VALUES (%s, %s, %s)', (order_id, product['id'], product['count'])
            self.cur.execute(*query)
            self.con.commit()
        for product in products:
            query = 'SELECT count_product from products where id = %s', (product['id'],)
            self.cur.execute(*query)
            count = self.prepare_data(self.cur.fetchall())[0]['count_product']
            query = f"UPDATE products SET count_product = '{count - product['count']}' where id = %s", (product['id'],)
            self.cur.execute(*query)
            self.con.commit()

    def getOrdersById(self, user_id):
        """Получение инфомрации о заказе по id"""
        query = 'SELECT * from orders where user_id = %s', (user_id,)
        self.cur.execute(*query)
        res = self.prepare_data(self.cur.fetchall())
        # print(res)
        if not res:
            print('Нет такого')
            return False
        return res

    def getOrderByNumber(self, num):
        """Получение информации о заказе по numder"""
        query = 'SELECT * from orders where number_order = %s', (num,)
        self.cur.execute(*query)
        res = self.prepare_data(self.cur.fetchall())
        if not res:
            print('Нет такого')
            return False
        return res[0]

    def getProductsIdByOrderId(self, order_id):
        """Получение айди продуктов из заказа order_id"""
        query = 'SELECT * from products_ordered where order_id = %s', (order_id,)
        self.cur.execute(*query)
        res = self.prepare_data(self.cur.fetchall())
        # print(res)
        if not res:
            print('Нет такого')
            return False
        return res

    def prepare_data(self, data):
        """Метод для подготовки выходных данных после запроса"""
        products = []
        if len(data):
            column_names = [desc[0] for desc in self.cur.description]
            for row in data:
                products += [{c_name: row[key] for key, c_name in enumerate(column_names)}]

        return products
