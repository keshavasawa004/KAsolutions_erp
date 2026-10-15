from sql_connection import get_sql_connection

def get_all_products(connection):
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT p.product_id, p.product_name as name, p.price_per_unit, p.cost_per_unit, p.stock_quantity, p.uom_id, u.uom_name 
        FROM products p 
        INNER JOIN uom u ON p.uom_id = u.uom_id;
    """
    cursor.execute(query)
    response = cursor.fetchall()
    cursor.close()
    return response

def insert_new_product(connection, product):
    cursor = connection.cursor()
    # Read the quantity from the frontend, default to 0 if missing
    qty = product.get('stock_quantity', 0) 
    
    # FIX 1: Changed 'name' to 'product_name' to match the database column
    query = ("INSERT INTO products "
             "(product_name, uom_id, price_per_unit, cost_per_unit, stock_quantity) "
             "VALUES (%s, %s, %s, %s, %s)")
    data = (product['product_name'], product['uom_id'], product['price_per_unit'], product['cost_per_unit'], qty)
    
    cursor.execute(query, data)
    connection.commit()
    return cursor.lastrowid

def delete_product(connection, product_id):
    cursor = connection.cursor()
    
    # FIX 2: Delete from order_details first to prevent Foreign Key constraint crashes
    cursor.execute("DELETE FROM order_details WHERE product_id = %s", (product_id,))
    
    # Now it is safe to delete the product
    query = "DELETE FROM products WHERE product_id = %s"
    cursor.execute(query, (product_id,))
    connection.commit()
    cursor.close()
    return cursor.lastrowid