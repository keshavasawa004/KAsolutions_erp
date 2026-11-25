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

# Explicitly allow requests & headers from your Render frontend
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"]
)

# --- JWT Security Configuration ---
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'local_dev_key_only')
jwt = JWTManager(app)
# ----------------------------------


@app.before_request
def handle_preflight():
    """Respond 200 OK immediately to browser CORS preflight OPTIONS checks."""
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response, 200


@app.after_request
def add_cors_headers(response):
    """Ensure every response—including 401/403/500 errors—carries CORS headers."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def check_is_admin(connection, username):
    """Case-insensitive check for admin role in database."""
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT role FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    return bool(user and str(user.get('role', '')).strip().lower() == 'admin')


@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "KA Solutions ERP Backend Live"}), 200


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


@app.route('/addExpense', methods=['POST'])
@jwt_required()
def add_expense():
    current_user = get_jwt_identity()
    connection = get_sql_connection()
    try:
        if not check_is_admin(connection, current_user):
            return jsonify({'error': 'Admin access required'}), 403

        request_payload = request.get_json()
        analytics_dao.insert_expense(connection, request_payload)
        return jsonify({'status': 'success'})
    except Exception as err:
        return jsonify({
            'error': 'Unable to add expense: ' + str(err),
            'status': 'failed'
        }), 400
    finally:
        connection.close()


@app.route('/deleteExpense', methods=['POST'])
@jwt_required()
def delete_expense():
    current_user = get_jwt_identity()
    connection = get_sql_connection()
    try:
        if not check_is_admin(connection, current_user):
            return jsonify({'error': 'Admin access required'}), 403

        expense_id = request.form['expense_id']
        analytics_dao.delete_expense(connection, expense_id)
        return jsonify({'status': 'success'})
    except Exception as err:
        return jsonify({
            'error': 'Unable to delete expense: ' + str(err),
            'status': 'failed'
        }), 400
    finally:
        connection.close()


if __name__ == '__main__':
    print("Starting Python Flask Server For Grocery Store Application...")
    app.run(port=5000)
