# Imported Modules
import os
from dotenv import load_dotenv
from models import Order
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from psycopg2 import pool
from datetime import datetime, timedelta
import jwt 
import uvicorn
import asyncio

# Local Modules
import queries as q
import pool
# from logging.handlers import RotatingFileHandler - stupid Vercel

load_dotenv()
SECRET_KEY=os.getenv('SECRET_KEY')

app = FastAPI()

# global variable to store and track running asynchronous tasks

TASK_DICT = dict()

# origins = [
#     "http://localhost/*",
#     "http://localhost:3000/*",
#     "http://localhost:3001/*",
#     "http://localhost:8080/*",
#     "https://rapid-ui.vercel.app/*"
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
This route is the base route for API

 Returns:
        Status message of API
"""
@app.get("/")
def root():
    return {"status":"Rapid Reservation API is running"}


"""
Authentication
"""
class User(BaseModel):
    user_id: int
    user_name: str
    password: str
    isadmin: bool



"""
Login route
"""
@app.post('/login')
async def login(request: Request):
    try:
        data = await request.json()
        username = data.get('username')
        password = data.get('password')
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.GET_USER_BY_USERNAME, (username,))
        connection.commit()
        user = cursor.fetchone()

        if user:
            if user[1] == username and user[2] == password:
                token_data = {
                    "user_id": user[0],
                    "user_name": user[1],
                    "expires_at": (datetime.utcnow() + timedelta(minutes=20)).isoformat()
                }
                jwt_token = jwt.encode(token_data, "50aa207b47293b1bf86b792a99cdc5a9bd55c6fb92010f156b9bbfd4c3e58bfd", algorithm="HS256")

                response_data = {
                    "message": "Login Successful",
                    "user": {
                        "user_id": user[0],
                        "user_name": user[1],
                        "isadmin": user[3]
                    },
                    "token": jwt_token
                }
                return response_data
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    finally:
        pool.release_connection(connection)




            





"""
TABLES
"""

"""
This is the auto reset function

"""
async def schedule_reset(table_number: int):
    try:
        await asyncio.sleep(3600) # Sleep for one hour. Change for testing.
        clear_table(table_number)
    except asyncio.CancelledError:
        print(f"Reset canceled.")
        raise

"""
This route is called when a table is reserved. Calls SET_RESERVATION script in queries.py

Returns:
    Success message on success

    Error message on error
"""
@app.post('/table/set/{table_number}')
async def reserve_table(table_number: int):
    try:
        connection = pool.get_connection()
        if table_number is not None:
            cursor = connection.cursor()
            cursor.execute(q.SET_RESERVATION, (table_number,))
            connection.commit()
            # TODO: Set BackgroundTask to wait 1 hour then reset the table
            task = asyncio.create_task(schedule_reset(table_number))
            TASK_DICT[table_number] = task
            try:
                await task
            except asyncio.CancelledError:
                print(f"Cancel was called")
            return {'success': True, 'message': 'Table reserved successfully'}
    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)
 
"""
This route can be called to make a table ready to be reserved again. Calls CLEAR_RESERVATION in queries.py

Returns:
        Success message on success

        Error message on Error
"""
@app.post('/table/clear/{table_number}')
def clear_table(table_number: int):

    try:
        connection = pool.get_connection()
        if table_number is not None:
            cursor = connection.cursor()
            cursor.execute(q.CLEAR_RESERVATION, (table_number,))
            connection.commit()
            # TODO: If table_number has an active countdown, it needs to be canceled
            try:
                task = TASK_DICT.pop(table_number)
                task.cancel()
            except:
                pass
            return {'success': True, 'message': 'Table cleared successfully'}
    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)

"""
This route can be called to make all table ready to be reserved again. Calls CLEAR_ALL_RESERVATIONS in queries.py

Returns:
        Success message on success

        Error message on Error
"""
@app.post('/table/clear_all/')
def clear_all_tables():

    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.CLEAR_ALL_RESERVATIONS)
        connection.commit()
        # TODO: Cancel all active countdowns
        try:
            for this_task in TASK_DICT.values():
                task = this_task
                task.cancel()
            TASK_DICT.clear()
        except:
            pass
        return {'success': True, 'message': 'Tables all cleared successfully'}
    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)

"""
This route is used to check the current status of a given table. Calls SELECT_RESERVATION from queries.py

Returns:
    Json with table information on success

    Error message on error
"""
@app.get('/table/{table_number}')
# @cache.cached(timeout=60)
def check_reservation(table_number: int):
    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.SELECT_RESERVATION, (table_number,))
        result = cursor.fetchall()

        table = [{'table_id': row[2],'order_id': row[0], 'max_customer': row[1], 'table_available': row[3]} for row in result]

        return table

    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)

"""
This route is used to pull all the data from all the tables. Calls GET_TABLE_INFO from queries.py

Returns:
    JSON of all table data on success

    Fail message on Failure
"""
@app.get('/table')
def get_table_info():
    tables = {}
    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.GET_TABLE_INFO)
        results = cursor.fetchall()
        
        tables = [{'table_id': row[2],'order_id': row[0], 'max_customer': row[1], 'table_available': row[3]} for row in results]
        return tables
    
    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)

"""
USERS
"""
@app.get('/users')
def get_user():
    """

    """
    users={}
    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.GET_ALL_USERS)
        results = cursor.fetchall()
        
        return [{"user_id": row[0], "user_name": row[1], "password": row[2], "isadmin": row[3]} for row in results]

    
    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)

@app.get('/customer/id/{email}')
def get_user_by_email(email: str):
    """

    """
    user={}
    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.GET_CUSTOMER_ID_BY_EMAIL, (email,))
        results = cursor.fetchall()
        
        return [{"user_id": row[0]} for row in results]

    
    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)

@app.post('/users/create')
async def new_customer(request: Request):
    """
    This route can be called to add a new customer. Calls CREATE_NEW_CUSTOMER in queries.py

    Returns:
        Success message on success

        Error message on Error
    """
    try:
        data = await request.json()
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        password = data.get('password')
        isadmin = data.get('isadmin')
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.CREATE_NEW_USER, ((user_id, user_name, password,isadmin)))
        connection.commit()
        return {'success': True, 'message': 'User {user_id} added successfully'}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail='Internal Server Error')

"""
CUSTOMERS
"""

@app.get('/customer')
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
        cursor.execute(q.GET_ALL_CUSTOMERS)
        results = cursor.fetchall()

        customers = [{'customer_id': row[4],'customer_name': row[0], 'customer_address': row[1], 'customer_phone': row[2], 'customer_email': row[3]} for row in results]
        return customers

    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)


@app.get('/customer/{customer_id}')
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
        cursor.execute(q.GET_CUSTOMER_BY_ID, (customer_id,))
        result = cursor.fetchall()

        customer = [{'customer_id': row[4],'customer_name': row[0], 'customer_address': row[1], 'customer_phone': row[2], 'customer_email': row[3]} for row in result]
        return customer

    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)


@app.post('/customer/set')
async def new_customer(request: Request):
    """
    This route can be called to add a new customer. Calls CREATE_NEW_CUSTOMER in queries.py
    Returns:

        Success message on success

        Error message on Error
    """
    try:
        data = await request.json()
        # TODO: add string sanitization here
        #customer_id = sanitize(data.get('customer_id'))
        customer_name = sanitize(data.get('customer_name'))
        customer_address = sanitize(data.get('customer_address'))
        customer_phone = sanitize(data.get('customer_phone'))
        customer_email = sanitize(data.get('customer_email'))
        print(customer_name + customer_address + customer_phone + customer_email)
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.CREATE_NEW_CUSTOMER, (customer_name, customer_address, customer_phone, customer_email,))
        connection.commit()
        return {'success': True, 'message': 'Customer added successfully'}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail='Internal Server Error')
    
"""
ORDERS
"""

@app.get("/orders")
def get_orders():
    """
  This route retrieves information about all orders.

  Returns:
      JSON with a list of order details on success.

      Error message on failure.
  """
    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.GET_ALL_ORDERS)
        orders = cursor.fetchall()
        cursor.execute(q.GET_ALL_ORDER_ITEMS)
        order_items = cursor.fetchall()
        return [
            {
                "order_id": row[6],
                "table_number": row[1],
                "customer_id": row[0],
                # Grab all of the food items and quantities from the ORDER_ITEMS table
                # add only those which belong to the current order_id
                "items": [
                    {
                        "food_id": order_item[0],
                        "quantity": order_item[2]
                    }

                    for order_item in order_items
                    if order_item[1] == row[0]
                ]
            }

            for row in orders
        ]
    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)


@app.get("/order/{order_id}")
def get_order(order_id: int):
    """
  This route retrieves information about a specific order.

  Args:
      order_id: The ID of the order to retrieve.
  Returns:
      JSON with order details on success.

      Error message on failure.
  """

    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.GET_ORDER_BY_ID, (order_id, ))
        order = cursor.fetchone()
        if order:
            cursor.execute(q.GET_ORDER_ITEMS_BY_ID, (order_id, ))
            order_items = cursor.fetchall()
            return {
                "order_id": order[6],
                "table_number": order[1],
                "customer_id": order[0],
                "items": [
                    {
                        "food_id": order_item[0],
                        "quantity": order_item[2]
                    }

                    for order_item in order_items
                ]
            }
        else:
            raise HTTPException(status_code=404, detail="Order not found")
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)


@app.post("/order/place")
async def place_order(request: Request, order: Order):
    """
  This route creates a new order.

  Args:
      request: The request object containing order details.
  Returns:
      JSON with success message on success.

      Error message on failure.
  """
    try:
        # Quick duplicate filter for order items
        # Will throw away an order item if it's associated food id is already present to avoid errors
        food_item_ids = []
        unique_food_items = []
        for order_item in order.items:
            if order_item.food_id not in food_item_ids:
                unique_food_items.append(order_item)
                food_item_ids.append(order_item.food_id)
        
        order.items = unique_food_items

        connection = pool.get_connection()
        cursor = connection.cursor()
        # Add order to 'public.order' table
        cursor.execute(q.CREATE_ORDER, (order.customer_id, order.table_number, ))
        order_id = cursor.fetchone()
        connection.commit()

        # Add each food item to 'public.order_items' table
        for order_item in order.items:
            cursor.execute(q.CREATE_ORDER_ITEM, (order_item.food_id, order_id, order_item.quantity, ))
            connection.commit()

        return {'success': True, 'message': 'Order placed successfully'}
    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)


def sanitize(incoming):
    """
    This function will sanitize incoming strings before they are inserted into the database to prevent data injection/
    Args:
        incoming: The incoming string.
    Returns:
        incoming: The sanitized string.
    """
    # Note: Doing these seperately for readability
    # Note: ampersand has to be first, else it will replace the correct display for the others
    incoming = incoming.replace("&" , "&#38;")
    incoming = incoming.replace("<" , "&#60;")
    incoming = incoming.replace(">" , "&#62;")
    incoming = incoming.replace('"' , "&#34;")
    incoming = incoming.replace("'" , "&#39;")
    return incoming

# @app.get('/test')
# def sanitize_test():
#     badstring = "<bad> '' &"
#     goodstring = sanitize(badstring)
#     return HTMLResponse(content=goodstring, status_code=200)

if __name__ == "__main__":
  uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)