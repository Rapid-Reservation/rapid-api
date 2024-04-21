"""
Creates an always open connection that prevents closing and reopening the access point which causes major delays.
"""
from psycopg2 import pool
from dotenv import load_dotenv
import os

# Load info from .env file
load_dotenv()

# Create a connection pool that always has atleast 1 connection, and can support up to 10. We can adjust as needed
connection_pool = pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    host=os.getenv('POSTGRES_HOST'),
    database=os.getenv('POSTGRES_DATABASE'),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)

# Functions to handle connection pools

# Grab a connection from pool
def get_connection():
    return connection_pool.getconn()

# Put connection back into pool
def release_connection(conn):
    connection_pool.putconn(conn)