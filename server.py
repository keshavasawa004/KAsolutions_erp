from flask import Flask, request, jsonify
import json
from sql_connection import get_sql_connection
from werkzeug.security import check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS

import products_dao
import uom_dao
import orders_dao
import analytics_dao
import os

app = Flask(__name__)
CORS(app)

# --- JWT Security Configuration ---
# In a real enterprise app, this secret key is hidden in a .env file.
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'local_dev_key_only')
jwt = JWTManager(app)
# ----------------------------------

@app.route('/login', methods=['POST'])
def login():
    # 1. Grab the username and password from the frontend JSON request
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
 
    connection = get_sql_connection()
    try:
        # 2. Look up the user in the database
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        # 3. If user exists AND the password matches the hash, issue a token
        if user and check_password_hash(user['password_hash'], password):
            
            # THE FIX: We must pass a STRING here, not a dictionary!
            access_token = create_access_token(identity=str(user['username']))
            
            response = jsonify({'token': access_token, 'role': user['role']})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200
        else:
            response = jsonify({'error': 'Invalid username or password'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 401
    finally:
        connection.close()

@app.route('/getProducts', methods=['GET'])
def get_products():
    connection = get_sql_connection()
    try:
        products = products_dao.get_all_products(connection)
        response = jsonify(products)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    finally:
        connection.close()

# NOTICE THE @jwt_required() DECORATOR HERE!
# This endpoint is now locked. It will reject any request missing a valid token.
@app.route('/deleteProduct', methods=['POST'])
@jwt_required()
def delete_product():
    connection = get_sql_connection()
    try:
        return_id = products_dao.delete_product(connection, request.form['product_id'])
        response = jsonify({'product_id': return_id})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    finally:
        connection.close()

@app.route('/getUOM', methods=['GET'])
def get_uom():
    connection = get_sql_connection()
    try:
        uoms = uom_dao.get_uoms(connection)
        response = jsonify(uoms)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    finally:
        connection.close()

@app.route('/insertProduct', methods=['POST'])
def insert_product():
    connection = get_sql_connection()
    try:
        request_payload = json.loads(request.form['data'])
        product_id = products_dao.insert_new_product(connection, request_payload)
        response = jsonify({'product_id': product_id})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    finally:
        connection.close()

@app.route('/insertOrder', methods=['POST'])
def insert_order():
    connection = get_sql_connection()
    try:
        request_payload = json.loads(request.form['data'])
        order_id = orders_dao.insert_order(connection, request_payload)
        response = jsonify({'order_id': order_id, 'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as err:
        response = jsonify({'error': str(err), 'status': 'failed'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    finally:
        connection.close()

@app.route('/getAllOrders', methods=['GET'])
def get_all_orders():
    connection = get_sql_connection()
    try:
        orders = orders_dao.get_all_orders(connection)
        response = jsonify(orders)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    finally:
        connection.close()

@app.route('/getAnalytics', methods=['GET'])
def get_analytics():
    connection = get_sql_connection()
    try:
        data = analytics_dao.get_store_analytics(connection)
        response = jsonify(data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    finally:
        connection.close()

@app.route('/getDailyProfit', methods=['GET'])
def get_daily_profit():
    connection = get_sql_connection()
    try:
        data = analytics_dao.get_daily_profit(connection)
        response = jsonify(data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    finally:
        connection.close()

@app.route('/getExpenses', methods=['GET'])
@jwt_required()
def get_expenses():
    connection = get_sql_connection()
    try:
        expenses = analytics_dao.get_all_expenses(connection)
        response = jsonify(expenses)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as err:
        response = jsonify({'error': str(err), 'status': 'failed'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    finally:
        connection.close()

@app.route('/addExpense', methods=['POST'])
@jwt_required()
def add_expense():
    connection = get_sql_connection()
    try:
        request_payload = request.get_json()
        analytics_dao.insert_expense(connection, request_payload)
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as err:
        # This will catch missing tables or database errors and send them to the frontend
        response = jsonify({'error': str(err), 'status': 'failed'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    finally:
        connection.close()
@app.route('/deleteExpense', methods=['POST'])
@jwt_required()
def delete_expense():
    connection = get_sql_connection()
    try:
        expense_id = request.form['expense_id']
        analytics_dao.delete_expense(connection, expense_id)
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as err:
        response = jsonify({'error': str(err), 'status': 'failed'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    finally:
        connection.close()
        
if __name__ == '__main__':
    print("Starting Python Flask Server For Grocery Store Application...")
    app.run(port=5000)