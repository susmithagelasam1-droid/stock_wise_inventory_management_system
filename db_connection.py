import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="susmitha@095",
        database="inventory management system"
    )
