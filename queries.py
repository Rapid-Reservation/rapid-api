"""
Collection of CONSTANTS that define sql queries.
"""

SET_RESERVATION = "UPDATE public.table SET table_available = False WHERE table_id = %s;"

CLEAR_RESERVATION = "UPDATE public.table SET table_available = True WHERE table_id = %s;"

SELECT_RESERVATION = "SELECT * FROM public.table WHERE table_id = %s;"

GET_TABLE_INFO = "SELECT * FROM public.table ORDER BY table_id;"
