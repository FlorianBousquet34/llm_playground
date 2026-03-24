from datetime import datetime
from typing import Any
import psycopg2
import os

"""
Helper for postgres and SQL
"""

def init_postgres():
    """
    Initialize a database connection
    """
    dbname = os.getenv("PG_DBNAME")
    user = os.getenv("PG_USER")
    password = os.getenv("PG_PASSWORD")
    host = os.getenv("PG_HOST")
    port = os.getenv("PG_PORT")
    connection = psycopg2.connect(database=dbname,
                            user=user,
                            password= password,
                            host= host,
                            port= port)
    return connection

def get_cursor(conn):
    """
    Get a cursor from the connection
    """
    return conn.cursor()

def insert(table, values: dict, conn):
    """
    Single dict insert into a database table
    """
    batch_insert(table, values, conn=conn)
    commit(conn)

def fetch_all(query: str, conn = None, cursor = None):
    """
    Fetch the query into a list of dict
    """
    csr = cursor
    if csr is None and conn is None:
        raise Exception('Missing postgres datasourse connection and cursor')
    if csr is None:
        csr = get_cursor(conn)
    csr.execute(query)
    return csr.fetchall()

def fetch_one(query: str, conn=None, cursor = None):
    """
    Fetch a single element of the query
    """
    csr = cursor
    if csr is None and conn is None:
        raise Exception('Missing postgres datasourse connection and cursor')
    if csr is None:
        csr = get_cursor(conn)
    csr.execute(query)
    return csr.fetchone()

def batch_insert(table, values: dict, conn = None, cursor = None) -> Any:
    """
    Used to insert in batch. Don't forget to commit !
    """
    csr = cursor
    if csr is None and conn is None:
        raise Exception('Missing postgres datasourse connection and cursor')
    elif csr is None:
        csr = get_cursor(conn)
    csr.execute("INSERT INTO " + table + "(" + ",".join(list(values.keys())) + ") VALUES (" + ",".join(['%s']*len(values.values())) + ")",
                tuple(values.values()))
    return csr
    
def format_type(val) -> str:
    """
    Parse python types into sql types
    """
    if isinstance(val, str):
        return "'"+ val + "'"
    elif isinstance(val, int) or isinstance(val, float):
        return str(val)
    elif(isinstance(val, datetime)):
        return "'" + datetime.strftime(val, '%Y-%m-%d %H:%M:%S.%f') + "'"
    else:
        raise Exception(f"Unknown postgres database type conversion val : {val} - type {type(val)}")
    
def commit(conn):
    """
    Commit the connection
    """
    conn.commit()

def close(conn):
    """
    Closes the connection
    """
    conn.close()