# Imported Modules
import os
from typing import Annotated
from dotenv import load_dotenv
from models import Order
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from psycopg2 import pool
from datetime import datetime, timedelta
from jose import JWTError, jwt  
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import uvicorn
# Local Modules
import queries as q
import pool
# from logging.handlers import RotatingFileHandler - stupid Vercel

load_dotenv()
app = FastAPI()

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
        Staus message of API
"""
@app.get("/")
def root():
    return {"status":"Rapid Reservation API is running"}


"""
Authentication
"""
class User(BaseModel):
    id: int
    email: str
    password: str
    isadmin: bool

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


SECRET_KEY=os.getenv('SECERT_KEY')
ALGORITHM=os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str):
    """
    Function takes a passed password and hashes it \n
    Returns:
        JSON of all table data on success
        Fail message on Failure
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """
    Function takes a passed password and password hashed and confirms they are the same
    Returns:
        JSON of all table data on success
        Fail message on Failure
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(datetime.UTC)+ expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to authenticate a user
def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not verify_password(password, user.get("password_hash")):
        return False
    return user


# Function to get a user from the database
def get_user(username: str):
    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.GET_USER_BY_USERNAME, (username))
        user_data = cursor.fetchone()

        if user_data:
            # Extract user data into a dictionary
            user = {
                "user_name": user_data[1],
                "password": user_data[2],
            }
            return user
        else:
            return None  # Return None if user not found
        
    finally:
        pool.release_connection(connection)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Endpoint for user login
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint for token refresh (if needed)
@app.post("/token/refresh")
async def refresh_access_token(current_user: User = Depends(get_current_user)):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": current_user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}




"""
TABLES
"""

"""
This route is called when a table is reserved. Calls SET_RESERVATION script in queries.py

Returns:
    Success message on success
    Error message on error
"""
@app.post('/table/set/{table_number}')
def reserve_table(table_number: int):

    try:
        connection = pool.get_connection()
        if table_number is not None:
            cursor = connection.cursor()
            cursor.execute(q.SET_RESERVATION, (table_number,))
            connection.commit()
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
            return {'success': True, 'message': 'Table reserved successfully'}
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
        return users
    
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

        customers = [{'customer_id': row[0],'customer_name': row[1], 'customer_address': row[2], 'customer_phone': row[3], 'customer_email': row[4]} for row in results]
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

        customer = [{'customer_id': row[0],'customer_name': row[1], 'customer_address': row[2], 'customer_phone': row[3], 'customer_email': row[4]} for row in result]

        return (customer)

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
        customer_id = data.get('customer_id')
        customer_name = data.get('customer_name')
        customer_address = data.get('customer_address')
        customer_phone = data.get('customer_phone')
        customer_email = data.get('customer_email')
        print(customer_name + customer_address + customer_phone + customer_email)
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.CREATE_NEW_CUSTOMER, (customer_id, customer_name, customer_address, customer_phone, customer_email,))
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
        return [{"order_id": row[0], "table_number": row[1], "customer_id": row[2], "items": row[3]} for row in orders]
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
        cursor.execute(q.GET_ORDER_BY_ID, (order_id))
        order = cursor.fetchone()
        if order:
            return {"order_id": order[0], "table_number": order[1], "customer_id": order[2], "items": order[3]}
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
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute(q.PLACE_ORDER, (order.table_number, order.customer_id, order.items,))
        connection.commit()
        return {'success': True, 'message': 'Order placed successfully'}
    except Exception as e:
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500
    finally:
        pool.release_connection(connection)


if __name__ == "__main__":
  uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)