# Table Item
from pydantic import BaseModel
 
"""
Table Data Object
    table_id: integer
    order_id: integer
    max_customer: integer
    table_avaliable: boolean
"""
class Table(BaseModel):
    table_id: int
    order_id: int
    max_customer: int
    table_avaliable: bool