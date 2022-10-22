import math
import time

import psycopg2
from psycopg2 import OperationalError

from flask_login import UserMixin


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
            query = f"SELECT id, product_name, text_info FROM products where " \
                    f"category='{cat}' and (product_name LIKE '%{search}%' or text_info LIKE '%{search}%')"
        elif cat:
            query = f"SELECT id, product_name, text_info FROM products where " \
                    f"category='{cat}'"
        elif search:
            query = f"SELECT id, product_name, text_info FROM products where " \
                    f"(product_name LIKE '%{search}%' or text_info LIKE '%{search}%')"
        else:
            query = f"SELECT id, product_name, text_info FROM products"

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
        query = f'SELECT * FROM products_categories'
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())
        if res:
            return res
        else:
            []

    def addProduct(self, product_name, text_info):
        tm = math.floor(time.time())
        query = f"INSERT INTO products (product_name, price, text_info) values ('{product_name}',{tm},'{text_info}')"
        self.cur.execute(query)
        self.con.commit()
        return True

    def getUser(self, user_id):
        query = f"SELECT * FROM users WHERE id = '{user_id}'"
        self.cur.execute(query)
        res = self.prepare_data(self.cur.fetchall())[0]
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

    def prepare_data(self, data):
        products = []
        if len(data):
            column_names = [desc[0] for desc in self.cur.description]
            for row in data:
                products += [{c_name: row[key] for key, c_name in enumerate(column_names)}]

        return products
