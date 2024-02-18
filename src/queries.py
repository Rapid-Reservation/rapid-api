INSERT_RESERVATION = "UPDATE public.table SET table_available = False WHERE table_id = %s;"

SELECT_RESERVATION = "SELECT * FROM public.table WHERE table_id = %s;"

GET_TABLE_INFO = "SELECT * FROM public.table;"
