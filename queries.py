"""
Collection of CONSTANTS that define sql queries.
"""

"""
User based queries
"""

GET_ALL_USERS = "SELECT * from public.user"
GET_USER_BY_ID = "SELECT * from public.user WHERE user_id = %s"
GET_USER_BY_USERNAME = "SELECT * from public.user WHERE user_name = %s"
CREATE_NEW_USER= "INSERT INTO public.user (user_id, user_name, password, isadmin) VALUES (%s, %s, %s, %s);"

"""
Table based queries
"""
SET_RESERVATION = "UPDATE public.table SET table_available = False WHERE table_id = %s;"

CLEAR_RESERVATION = "UPDATE public.table SET table_available = True WHERE table_id = %s;"

SELECT_RESERVATION = "SELECT * FROM public.table WHERE table_id = %s;"

GET_TABLE_INFO = "SELECT * FROM public.table ORDER BY table_id;"

""" Customer Based Queries"""
GET_ALL_CUSTOMERS = "SELECT * FROM public.customer ORDER BY customer_id;"

GET_CUSTOMER_BY_ID = "SELECT * FROM public.customer WHERE customer_id = %s;"

CREATE_NEW_CUSTOMER = "INSERT INTO public.customer (customer_id, customer_name, customer_address, customer_phone, customer_email) VALUES (%s, %s, %s, %s, %s);"


""" Order based Queries"""
GET_ALL_ORDERS = "SELECT * FROM orders;"

GET_ORDER_BY_ID = "SELECT * FROM orders WHERE order_id = %s;"

PLACE_ORDER = "INSERT INTO orders (table_number, customer_id, items) VALUES (%s, %s, %s);"