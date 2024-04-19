"""
Collection of CONSTANTS that define sql queries.
"""

SET_RESERVATION = "UPDATE public.table SET table_available = False WHERE table_id = %s;"

CLEAR_RESERVATION = "UPDATE public.table SET table_available = True WHERE table_id = %s;"

SELECT_RESERVATION = "SELECT * FROM public.table WHERE table_id = %s;"

GET_TABLE_INFO = "SELECT * FROM public.table ORDER BY table_id;"

GET_ALL_CUSTOMERS = "SELECT * FROM public.customer ORDER BY customer_id;"

GET_CUSTOMER_BY_ID = "SELECT * FROM public.customer WHERE customer_id = %s;"

CREATE_NEW_CUSTOMER = "INSERT INTO public.customer (customer_id, customer_name, customer_address, customer_phone, customer_email) VALUES (%s, %s, %s, %s, %s);"

GET_ALL_ORDERS = "SELECT * FROM order;"

GET_ALL_ORDER_ITEMS = "SELECT * FROM order_items;"

GET_ORDER_ITEMS = "SELECT * FROM order_items WHERE order_id = %s"

GET_ORDER_BY_ID = "SELECT * FROM order WHERE order_id = %s;"

PLACE_ORDER = "INSERT INTO orders (table_number, customer_id, items) VALUES (%s, %s, %s);"