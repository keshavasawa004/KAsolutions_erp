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
    qty = float(product.get('stock_quantity') or 0)
    uom_id = int(product['uom_id'])
    price = float(product['price_per_unit'])
    cost = float(product['cost_per_unit'])

    query = """
        INSERT INTO products 
        (product_name, uom_id, price_per_unit, cost_per_unit, stock_quantity) 
        VALUES (%s, %s, %s, %s, %s)
    """
    data = (product['product_name'].strip(), uom_id, price, cost, qty)
    
    cursor.execute(query, data)
    connection.commit()
    last_id = cursor.lastrowid
    cursor.close()
    return last_id

def delete_product(connection, product_id):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM order_details WHERE product_id = %s", (product_id,))
    cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
    connection.commit()
    cursor.close()
    return product_id

def update_product(connection, product):
    cursor = connection.cursor()
    # FIXED: Changed 'name' to 'product_name' to match your MySQL schema
    query = """
        UPDATE products 
        SET product_name = %s, cost_per_unit = %s, price_per_unit = %s, stock_quantity = %s
        WHERE product_id = %s
    """
    data = (
        product['product_name'].strip(),
        float(product['cost_per_unit']),
        float(product['price_per_unit']),
        float(product['stock_quantity']),
        int(product['product_id'])
    )
    cursor.execute(query, data)
    connection.commit()
    cursor.close()
    return product['product_id']
