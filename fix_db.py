from sql_connection import get_sql_connection

def fix_database():
    print("Connecting to the database...")
    connection = get_sql_connection()
    cursor = connection.cursor()
    
    try:
        # 1. Drop the table if it is corrupted
        print("Dropping old expenses table (if it exists)...")
        cursor.execute("DROP TABLE IF EXISTS expenses;")
        
        # 2. Force create the table in the correct schema
        print("Creating fresh expenses table...")
        cursor.execute("""
            CREATE TABLE expenses (
                expense_id INT AUTO_INCREMENT PRIMARY KEY,
                expense_date DATE NOT NULL,
                expense_category VARCHAR(100) NOT NULL,
                amount DECIMAL(10,2) NOT NULL
            );
        """)
        
        connection.commit()
        print("SUCCESS: The expenses table is ready to go!")
        
    except Exception as e:
        print(f"FAILED: An error occurred: {e}")
        
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    fix_database()