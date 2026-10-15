from datetime import datetime

def insert_order(connection, order):
    cursor = connection.cursor()

    # 1. Insert the main order record
    order_query = "INSERT INTO orders (customer_name, total, datetime) VALUES (%s, %s, %s)"
    order_data = (order['customer_name'], order['grand_total'], datetime.now())
    cursor.execute(order_query, order_data)
    order_id = cursor.lastrowid

    # 2. Insert the order details and update stock
    order_details_query = "INSERT INTO order_details (order_id, product_id, quantity, total_price) VALUES (%s, %s, %s, %s)"
    stock_update_query = "UPDATE products SET stock_quantity = stock_quantity - %s WHERE product_id = %s"
    
    for item in order['order_details']:
        # Add to order details
        cursor.execute(order_details_query, (order_id, item['product_id'], item['quantity'], item['total_price']))
        # Deduct from inventory
        cursor.execute(stock_update_query, (item['quantity'], item['product_id']))

    # 3. Commit the transaction
    connection.commit()
    cursor.close()
    
    return order_id

def get_all_orders(connection):
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM orders ORDER BY datetime DESC LIMIT 50"
    cursor.execute(query)
    response = cursor.fetchall()
    
    # Format datetimes for JSON compatibility
    for row in response:
        row['datetime'] = str(row['datetime'])
        row['total'] = float(row['total'])
        
    cursor.close()
    return response