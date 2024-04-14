# Table Item
from pydantic import BaseModel
from typing import List
 
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


class Order(BaseModel):
    table_number: int
    customer_id: int
    items: List[str]
