from sql_connection import get_sql_connection

def get_store_analytics(connection):
    cursor = connection.cursor(dictionary=True)

    # 1. Calculate Total Revenue and Total Cost of Goods Sold
    sales_query = """
        SELECT 
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM(od.total_price), 0) AS total_revenue,
            COALESCE(SUM(od.quantity * p.cost_per_unit), 0) AS total_cost
        FROM orders o
        LEFT JOIN order_details od ON o.order_id = od.order_id
        LEFT JOIN products p ON od.product_id = p.product_id;
    """
    cursor.execute(sales_query)
    sales_data = cursor.fetchone()

    # 2. Calculate Total Additional Expenses
    expense_query = "SELECT COALESCE(SUM(amount), 0) as total_expenses FROM expenses;"
    cursor.execute(expense_query)
    expense_data = cursor.fetchone()
    
    # 3. Do the final math
    total_revenue = float(sales_data['total_revenue'] if sales_data['total_revenue'] else 0)
    total_cost = float(sales_data['total_cost'] if sales_data['total_cost'] else 0)
    total_expenses = float(expense_data['total_expenses'] if expense_data['total_expenses'] else 0)
    
    # EXACT NET PROFIT
    net_profit = total_revenue - total_cost - total_expenses

    kpis = {
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_expenses': total_expenses,
        'net_profit': net_profit
    }

    cursor.close()
    return {'kpis': kpis}

def get_daily_profit(connection):
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT 
            sales.order_date,
            sales.daily_revenue,
            sales.daily_cost,
            COALESCE(e.daily_expense, 0) as daily_expense,
            (sales.daily_revenue - sales.daily_cost) AS gross_profit,
            (sales.daily_revenue - sales.daily_cost - COALESCE(e.daily_expense, 0)) AS net_profit
        FROM (
            SELECT 
                DATE(o.datetime) as order_date,
                SUM(od.total_price) as daily_revenue,
                SUM(od.quantity * p.cost_per_unit) as daily_cost
            FROM orders o
            JOIN order_details od ON o.order_id = od.order_id
            JOIN products p ON od.product_id = p.product_id
            GROUP BY DATE(o.datetime)
        ) sales
        LEFT JOIN (
            SELECT expense_date, SUM(amount) as daily_expense
            FROM expenses
            GROUP BY expense_date
        ) e ON sales.order_date = e.expense_date
        ORDER BY sales.order_date DESC
        LIMIT 7;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    
    for row in results:
        row['order_date'] = str(row['order_date'])
        row['daily_revenue'] = float(row['daily_revenue'] or 0)
        row['daily_cost'] = float(row['daily_cost'] or 0)
        row['daily_expense'] = float(row['daily_expense'] or 0)
        row['gross_profit'] = float(row['gross_profit'] or 0)
        row['net_profit'] = float(row['net_profit'] or 0)
        
    cursor.close()
    return results

def insert_expense(connection, expense_data):
    cursor = connection.cursor()
    query = "INSERT INTO expenses (expense_date, expense_category, amount) VALUES (%s, %s, %s)"
    cursor.execute(query, (expense_data['date'], expense_data['category'], expense_data['amount']))
    connection.commit()
    cursor.close()
    return True

def get_all_expenses(connection):
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT expense_id, DATE_FORMAT(expense_date, '%Y-%m-%d') as expense_date, expense_category, amount 
        FROM expenses 
        ORDER BY expense_date DESC, expense_id DESC 
        LIMIT 50;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    for row in results:
        row['amount'] = float(row['amount'])
    cursor.close()
    return results

def delete_expense(connection, expense_id):
    cursor = connection.cursor()
    query = "DELETE FROM expenses WHERE expense_id = %s"
    cursor.execute(query, (expense_id,))
    connection.commit()
    cursor.close()
    return True