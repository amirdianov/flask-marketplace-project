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
    def fromDB(self, user_id, db):
        self.__user = db.getUser(user_id)
        return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user['id'])

    def get_category(self):
        return str(self.__user['category'])

    def getAvatar(self, app):
        img = None
        if not self.__user['profile']:
            with app.open_resource(app.root_path + url_for('static', filename='media/profiles/default_avatar.png'),
                                   'rb') as f:
                img = f.read()
                print(img)
        else:
            img = self.__user['profile']
            with app.open_resource(app.root_path + url_for('static', filename=f'media/profiles/{img}'),
                                   'rb') as f:
                img = f.read()
        return img

    def verifyExt(self, filename):
        ext = filename.rsplit('.', 1)[1]
        if ext == "png" or ext == "PNG":
            return True
        return False


class Database:
    def __init__(self):
        self.con = psycopg2.connect(
            dbname="marketplace_db",
            user="postgres",
            password="Amir2003",
            host="localhost",
            port=5432
        )
        self.cur = self.con.cursor()

    def getProducts(self, cat, search):
        # query = f"SELECT id, product_name, text_info FROM products"

        if cat and search:
            query = f"SELECT * FROM products where " \
                    f"category='{cat}' and count_product > 0 and (product_name LIKE '%{search}%' or text_info LIKE '%{search}%' order by id asc)"
        elif cat:
            query = f"SELECT * FROM products where " \
                    f"category='{cat}'and count_product > 0 order by id asc"
        elif search:
            query = f"SELECT * FROM products where count_product > 0  and " \
                    f"(product_name LIKE '%{search}%' or text_info LIKE '%{search}%') order by id asc"
        else:
            query = f"SELECT * FROM products where count_product > 0 order by id asc"

        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())
        if res:
            return res
        return []

    def getProductById(self, product_id):
        query = f"SELECT * FROM products where id='{product_id}'"
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())
        if res:
            return res[0]
        return []

    def getCategories(self):
        query = f'SELECT * FROM products_categories order by category_name'
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())
        if res:
            return res
        else:
            return []

    def getPhoto(self, product_id):
        query = f"SELECT * FROM products where id={product_id}"
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())[0]
        img = r'C:\Users\amird\PycharmProjects\flask-marketplace-project' + res['image_path']
        with open(img, 'rb') as f:
            img = f.read()
        return img

    def add_edit_Product(self, type_operation, product_name, price, text_info, image_path, category, count_product,
                         product_id=None):
        if type_operation == 'add':
            query = f"INSERT INTO products (product_name, price, text_info, image_path, category, count_product)" \
                    f" values ('{product_name}',{price},'{text_info}', '{image_path}', '{category}', '{count_product}')"
            self.cur.execute(query)
            self.con.commit()
            return True
        else:
            query = f"UPDATE products SET product_name = '{product_name}' where id = {product_id};" \
                    f"UPDATE products SET price = '{price}' where id = {product_id};" \
                    f"UPDATE products SET text_info = '{text_info}' where id = {product_id};" \
                    f"UPDATE products SET image_path = '{image_path}' where id = {product_id};" \
                    f"UPDATE products SET category = '{category}' where id = {product_id};" \
                    f"UPDATE products SET count_product = '{count_product}' where id = {product_id};"
            self.cur.execute(query)
            self.con.commit()
            return True

    def deleteProductById(self, product_id):
        query = f"UPDATE products SET count_product = 0 where id = {product_id} "
        self.cur.execute(query)
        self.con.commit()
        return True

    def deleteProductPhoto(self, get_id):
        query = f"SELECT image_path FROM products WHERE id = '{get_id}'"
        self.cur.execute(query)
        filename = self.prepare_data(self.cur.fetchall())[0]
        if filename['image_path']:
            return filename['image_path']

    def getUser(self, user_id):
        query = f"SELECT * FROM users WHERE id = '{user_id}'"
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())[0]
        if not res:
            print('Нет такого')
            return False
        return res

    def getUsers(self):
        query = f"SELECT * FROM users"
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())
        if not res:
            print('Нет такого')
            return False
        return res

    def getUserByEmail(self, email):
        query = f"SELECT * FROM users WHERE email = '{email}'"
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())[0]
        if not res:
            print('Нет такого')
            return False
        return res

    def getUsersCategory(self, email, password):
        query = f"SELECT * FROM users WHERE email = '{email}'"
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())[0]
        print(res)
        pas = res['password']
        if not res:
            print('Нет такого')
            return False
        print(pas)
        if check_password_hash(pas, password):
            print('СОШЛОСЬ')
            return res['category']

    def addUser(self, email, psw):
        query = f"SELECT COUNT(*) as count FROM users WHERE email LIKE '{email}'"
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())
        print(res)
        if res[0]['count'] > 0:
            print("Пользователь с таким email уже существует")
            return False

        # tm = math.floor(time.time())
        query = f"INSERT INTO users (email, password) VALUES ('{email}', '{psw}')"
        self.cur.execute(query)
        self.con.commit()
        return True

    def editUser(self, user_id, email, psw=None):
        query = f"UPDATE users SET email = '{email}' where id = '{user_id}';"
        if psw:
            query += f"UPDATE users SET password = '{psw}' where id = '{user_id}';"
        self.cur.execute(query)
        self.con.commit()
        return True

    def updateUserAvatar(self, avatar, user_id):
        if not avatar:
            return False
        self.cur.execute(f"UPDATE users SET profile = '{avatar}' where id = {user_id}")
        self.con.commit()
        return True

    def deleteUserAvatar(self, get_id):
        query = f"SELECT profile FROM users WHERE id = '{get_id}'"
        self.cur.execute(query)
        filename = self.prepare_data(self.cur.fetchall())[0]
        if filename['profile']:
            return filename['profile']

    def changeUserCategory(self, id_user_to_change, new_category):
        query = f"UPDATE users SET category = '{new_category}' where id={id_user_to_change}"
        self.cur.execute(query)
        self.con.commit()

    def makeOrder(self, user_id, products, address):
        now = datetime.datetime.now()
        id_products = []
        sum_products = 0
        number = random.randint(10000, 99999)
        for product in products:
            id_products.append(product['id'])
            sum_products = sum_products + product['count'] * product['price']
        query = f"INSERT INTO orders (user_id, sum_products, time_now, address, number_order) " \
                f"VALUES ('{user_id}', '{sum_products}', '{now}', '{address}', '{number}')"
        self.cur.execute(query)
        self.con.commit()
        query_again = f"SELECT id FROM orders WHERE number_order = '{number}'"
        self.cur.execute(query_again)
        order_id = self.prepare_data(self.cur.fetchall())[0]['id']
        print(order_id)
        for product in products:
            query = f"INSERT INTO products_ordered (order_id, product_id, count_product) " \
                    f"VALUES ('{order_id}', '{product['id']}', '{product['count']}')"
            self.cur.execute(query)
            self.con.commit()
        for product in products:
            query = f"SELECT count_product from products where id = '{product['id']}'"
            self.cur.execute(query)
            count = self.prepare_data(self.cur.fetchall())[0]['count_product']
            query = f"UPDATE products SET count_product = '{count - product['count']}' where id = '{product['id']}'"
            self.cur.execute(query)
            self.con.commit()

    def getOrdersById(self, user_id):
        query = f"SELECT * from orders where user_id = '{user_id}'"
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())
        print(res)
        if not res:
            print('Нет такого')
            return False
        return res

    def getOrderByNumber(self, num):
        query = f"SELECT * from orders where number_order = '{num}'"
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())[0]
        print(res)
        if not res:
            print('Нет такого')
            return False
        return res

    def getProductsIdByOrderId(self, order_id):
        query = f"SELECT * from products_ordered where order_id = '{order_id}'"
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())
        print(res)
        if not res:
            print('Нет такого')
            return False
        return res

    def prepare_data(self, data):
        products = []
        if len(data):
            column_names = [desc[0] for desc in self.cur.description]
            for row in data:
                products += [{c_name: row[key] for key, c_name in enumerate(column_names)}]

        return products
