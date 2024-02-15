from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

from queries import INSERT_RESERVATION, SELECT_RESERVATION, GET_TABLE_INFO

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DATABASE")
    )
@app.route('/')
def index():
    return "Rapid Reservation API is running"

@app.route('/table', methods=['POST'])
def reserve_table():
    connection = None 
    try:
        data = request.get_json()
        table_number = data.get('table_number')

        if table_number is not None:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(INSERT_RESERVATION, (table_number,))
            connection.commit()

            return jsonify({'success': True, 'message': 'Table reserved successfully'})

        return jsonify({'error': 'Invalid request'}), 400

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

    finally:
        if connection:
            connection.close()

@app.route('/table/<int:table_number>', methods=['GET'])
def check_reservation(table_number):
    connection = get_db_connection() 
    try:
        cursor = connection.cursor()
        cursor.execute(SELECT_RESERVATION, (table_number,))
        result = cursor.fetchone()

        return jsonify({'is_reserved': result[1]})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

    finally:
        if connection:
            connection.close()
            
@app.route('/table', methods=['GET'])
def get_table_info():
    connection = get_db_connection() 
    try:
        cursor = connection.cursor()
        cursor.execute(GET_TABLE_INFO)
        results = cursor.fetchall()
        
        tables = [{'id': row[0], 'reserved': row[1]} for row in results]

        return jsonify({'tables': tables})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    app.run(debug=True)
