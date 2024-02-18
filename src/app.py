from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify

from flask_cors import CORS
from flask_caching import Cache
from psycopg2 import pool

# Local Modules
from queries import INSERT_RESERVATION, SELECT_RESERVATION, GET_TABLE_INFO
import pool
import logger


app = Flask(__name__)

CORS(app) # Allows for Cross-Origin Resource Sharing - Removing this stops the front end components from using data from api

cache = Cache(app, config={'CACHE_TYPE':'simple'}) # Creates simple in-app cache, can potentially move to redis based cache?

@app.route('/')
def index():
    return "Rapid Reservation API is running"

@app.route('/table', methods=['POST'])
def reserve_table():
    try:
        connection = pool.get_connection()
        data = request.get_json()
        table_number = data.get('table_id')

        if table_number is not None:
            cursor = connection.cursor()
            cursor.execute(INSERT_RESERVATION, (table_number,))
            connection.commit()
            return jsonify({'success': True, 'message': 'Table reserved successfully'})

        return jsonify({'error': 'Invalid request'}), 400
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        pool.release_connection(connection)


@app.route('/table/<int:table_number>', methods=['GET'])
@cache.cached(timeout=60)
def check_reservation(table_number):
    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(SELECT_RESERVATION, (table_number,))
        result = cursor.fetchall()

        table = [{'table_id': row[2],'order_id': row[0], 'max_customer': row[1], 'table_available': row[3]} for row in result]

        return jsonify(table)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        pool.release_connection(connection)

            
@app.route('/table', methods=['GET'])
@cache.cached(timeout=60)  # Cache for 1 minute, need to discuss ideal time or convert to redis db cache
def get_table_info():
    tables = {}
    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(GET_TABLE_INFO)
        results = cursor.fetchall()
        
        tables = [{'table_id': row[2],'order_id': row[0], 'max_customer': row[1], 'table_available': row[3]} for row in results]
        return jsonify(tables)
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        pool.release_connection(connection)

if __name__ == '__main__':
    app.run(debug=True)
