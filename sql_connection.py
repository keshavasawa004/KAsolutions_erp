import os
import mysql.connector
from mysql.connector import pooling

__pool = None

def get_sql_connection():
    global __pool
    if __pool is None:
        db_host = os.environ.get('DB_HOST', '127.0.0.1')
        db_user = os.environ.get('DB_USER', 'root')
        db_password = os.environ.get('DB_PASSWORD', 'password')  # Your local password
        db_name = os.environ.get('DB_NAME', 'grocery_database')
        db_port = int(os.environ.get('DB_PORT', '3306'))

        is_cloud = (db_host != '127.0.0.1' and db_host != 'localhost')

        pool_config = {
            "pool_name": "grocery_pool",
            "pool_size": 10,
            "pool_reset_session": True,
            "host": db_host,
            "user": db_user,
            "password": db_password,
            "database": db_name,
            "port": db_port,
        }

        # TiDB requires SSL; local MySQL usually runs without it
        if is_cloud:
            pool_config["ssl_verify_cert"] = False
        else:
            pool_config["ssl_disabled"] = True

        __pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
        
    return __pool.get_connection()