from werkzeug.security import generate_password_hash
from sql_connection import get_sql_connection

def create_admin():
    connection = get_sql_connection()
    cursor = connection.cursor()

    # The credentials you will use to log in
    username = "admin"
    raw_password = "adminpassword123" 

    # Scramble the password securely
    hashed_pw = generate_password_hash(raw_password) 

    try:
        query = "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, hashed_pw, 'admin'))
        connection.commit()
        print(f"Success! User '{username}' created with encrypted password.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    create_admin()