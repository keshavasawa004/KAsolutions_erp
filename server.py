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

CORS(
    app,
    resources={r"/*": {"origins": ["https://kasolutions-erp-1.onrender.com", "*"]}},
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"]
)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return response, 200

# --- JWT Security Configuration ---
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'local_dev_key_only')
jwt = JWTManager(app)
# ----------------------------------


def check_is_admin(connection, username):
    """Helper to verify if the authenticated user has admin privileges."""
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT role FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    return bool(user and user.get('role') == 'admin')


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    connection = get_sql_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password_hash'], password):
            access_token = create_access_token(identity=str(user['username']))
            return jsonify({
                'token': access_token,
                'role': user['role']
            }), 200

        return jsonify({'error': 'Invalid username or password'}), 401
    finally:
        connection.close()


@app.route('/getProducts', methods=['GET'])
@jwt_required()
def get_products():
    connection = get_sql_connection()
    try:
        products = products_dao.get_all_products(connection)
        return jsonify(products)
    finally:
        connection.close()


@app.route('/insertProduct', methods=['POST'])
@jwt_required()
def insert_product():
    current_user = get_jwt_identity()
    connection = get_sql_connection()
    try:
        if not check_is_admin(connection, current_user):
            return jsonify({'error': 'Admin access required'}), 403

        request_payload = json.loads(request.form['data'])
        product_id = products_dao.insert_new_product(connection, request_payload)
        return jsonify({'product_id': product_id, 'status': 'success'})
    except Exception as err:
        return jsonify({'error': str(err), 'status': 'failed'}), 400
    finally:
        connection.close()


# NEW: Route for Admin Edit / Restock Modal
@app.route('/updateProduct', methods=['POST'])
@jwt_required()
def update_product():
    current_user = get_jwt_identity()
    connection = get_sql_connection()
    try:
        if not check_is_admin(connection, current_user):
            return jsonify({'error': 'Admin access required'}), 403

        request_payload = json.loads(request.form['data'])
        product_id = products_dao.update_product(connection, request_payload)
        return jsonify({'product_id': product_id, 'status': 'success'})
    except Exception as err:
        return jsonify({'error': str(err), 'status': 'failed'}), 400
    finally:
        connection.close()


# FIXED: Now restricted to Admin role only
@app.route('/deleteProduct', methods=['POST'])
@jwt_required()
def delete_product():
    current_user = get_jwt_identity()
    connection = get_sql_connection()
    try:
        if not check_is_admin(connection, current_user):
            return jsonify({'error': 'Admin access required'}), 403

        return_id = products_dao.delete_product(connection, request.form['product_id'])
        return jsonify({'product_id': return_id, 'status': 'success'})
    except Exception as err:
        return jsonify({'error': str(err), 'status': 'failed'}), 400
    finally:
        connection.close()


@app.route('/getUOM', methods=['GET'])
@jwt_required()
def get_uom():
    connection = get_sql_connection()
    try:
        uoms = uom_dao.get_uoms(connection)
        return jsonify(uoms)
    finally:
        connection.close()


@app.route('/insertOrder', methods=['POST'])
@jwt_required()
def insert_order():
    connection = get_sql_connection()
    try:
        request_payload = json.loads(request.form['data'])
        order_id = orders_dao.insert_order(connection, request_payload)
        return jsonify({
            'order_id': order_id,
            'status': 'success'
        })
    except Exception as err:
        return jsonify({
            'error': 'Unable to create order: ' + str(err),
            'status': 'failed'
        }), 400
    finally:
        connection.close()


@app.route('/getAllOrders', methods=['GET'])
@jwt_required()
def get_all_orders():
    connection = get_sql_connection()
    try:
        orders = orders_dao.get_all_orders(connection)
        return jsonify(orders)
    finally:
        connection.close()


@app.route('/getAnalytics', methods=['GET'])
@jwt_required()
def get_analytics():
    connection = get_sql_connection()
    try:
        data = analytics_dao.get_store_analytics(connection)
        return jsonify(data)
    finally:
        connection.close()


@app.route('/getDailyProfit', methods=['GET'])
@jwt_required()
def get_daily_profit():
    connection = get_sql_connection()
    try:
        data = analytics_dao.get_daily_profit(connection)
        return jsonify(data)
    finally:
        connection.close()


@app.route('/getExpenses', methods=['GET'])
@jwt_required()
def get_expenses():
    connection = get_sql_connection()
    try:
        expenses = analytics_dao.get_all_expenses(connection)
        return jsonify(expenses)
    except Exception as err:
        return jsonify({'error': str(err), 'status': 'failed'}), 400
    finally:
        connection.close()
