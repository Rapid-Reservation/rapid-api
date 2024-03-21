"""

Primary access point for the rapid-api.  Uses Flash to set routes that the ui can point to.

"""


from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify

from flask_cors import CORS, cross_origin
from flask_caching import Cache
from psycopg2 import pool

# Local Modules
from queries import SET_RESERVATION, SELECT_RESERVATION, GET_TABLE_INFO, CLEAR_RESERVATION, GET_ALL_CUSTOMERS, GET_CUSTOMER_BY_ID, CREATE_NEW_CUSTOMER
import pool
import logger


app = Flask(__name__)

CORS(app=app, resources={r"/*": {"origins": "*"}}, send_wildcard=True) # Allows for Cross-Origin Resource Sharing - Removing this stops the front end components from using data from api

cache = Cache(app, config={'CACHE_TYPE':'simple'}) # Creates simple in-app cache, can potentially move to redis based cache?

@app.route('/')
def index():
    """
    This route exists to confirm the successful deployment of the api.

    Returns:
        Confirmation message
    """
    return "Rapid Reservation API is running"

@app.route('/table/set/<int:table_number>', methods=['POST'])
@cross_origin()
def reserve_table(table_number):
    """
    This route is called when a table is reserved. Calls SET_RESERVATION script in queries.py

    Returns:
        Success message on success
        Error message on error
    """
    try:
        connection = pool.get_connection()
        if table_number is not None:
            cursor = connection.cursor()
            cursor.execute(SET_RESERVATION, (table_number,))
            connection.commit()
            return jsonify({'success': True, 'message': 'Table reserved successfully'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        pool.release_connection(connection)

@app.route('/table/clear/<int:table_number>', methods=['POST'])
@cross_origin()
def clear_table(table_number):
    """
    This route can be called to make a table ready to be reserved again. Calls CLEAR_RESERVATION in queries.py

    Returns:
        Success message on success
        Error message on Error
    """
    try:
        connection = pool.get_connection()
        if table_number is not None:
            cursor = connection.cursor()
            cursor.execute(CLEAR_RESERVATION, (table_number,))
            connection.commit()
            return jsonify({'success': True, 'message': 'Table reserved successfully'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        pool.release_connection(connection)


@app.route('/table/<int:table_number>', methods=['GET'])
# @cache.cached(timeout=60)
def check_reservation(table_number):
    """
    This route is used to check the current status of a given table. Calls SELECT_RESERVATION from queries.py

    Returns:
        Json with table information on success
        Error message on error
    """
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
#@cache.cached(timeout=60)  # Cache for 1 minute, need to discuss ideal time or convert to redis db cache
def get_table_info():
    """
    This route is used to pull all the data from all the tables. Calls GET_TABLE_INFO from queries.py

    Returns:
        Json of all table data on success
        Fail message on Failure
    """
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

@app.route('/customer', methods=['GET'])
def get_customer_info():
    """
    This route is used to pull all the data from all the customers. Calls GET_ALL_CUSTOMERS from queries.py

    Returns:
        Json of all customer data on success
        Fail message on Failure
    """
    customers = {}
    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(GET_ALL_CUSTOMERS)
        results = cursor.fetchall()
        
        customers = [{'customer_id': row[0],'customer_name': row[1], 'customer_address': row[2], 'customer_phone': row[3], 'customer_email': row[4]} for row in results]
        return jsonify(customers)
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        pool.release_connection(connection)
    

@app.route('/customer/<int:customer_id>', methods=['GET'])
def get_one_customer_info(customer_id):
    """
    This route is used to return a single customers information. Calls GET_CUSTOMER_BY_ID from queries.py

    Returns:
        Json with customer information on success
        Error message on error
    """
    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(GET_CUSTOMER_BY_ID, (customer_id,))
        result = cursor.fetchall()

        customer = [{'customer_id': row[0],'customer_name': row[1], 'customer_address': row[2], 'customer_phone': row[3], 'customer_email': row[4]} for row in result]

        return jsonify(customer)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        pool.release_connection(connection)


@app.route('/customer/set', methods=['POST'])
# @cross_origin()
def new_customer():
    """
    This route can be called to add a new customer. Calls CREATE_NEW_CUSTOMER in queries.py

    Returns:
        Success message on success
        Error message on Error
    """
    try:
        data = request.json
        customer_id = data.get('customer_id')
        customer_name = data.get('customer_name')
        customer_address = data.get('customer_address')
        customer_phone = data.get('customer_phone')
        customer_email = data.get('customer_email')
        print(customer_name + customer_address + customer_phone + customer_email)
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(CREATE_NEW_CUSTOMER, (customer_id, customer_name, customer_address, customer_phone, customer_email,))
        connection.commit()
        return jsonify({'success': True, 'message': 'Customer added successfully'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    # finally:
        # pool.release_connection(connection)


if __name__ == '__main__':
    app.run(debug=True)
