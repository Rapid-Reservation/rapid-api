INSERT_RESERVATION = "INSERT INTO public.table (table_id) VALUES (%s);"

SELECT_RESERVATION = "SELECT table_id, table_available FROM public.table WHERE table_id = %s;"

GET_TABLE_INFO = "SELECT table_id, table_available FROM public.table;"
