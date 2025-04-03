from typing import Union
import polars as pl
from fastapi import FastAPI
from os.path import join

app = FastAPI()
data_dir = join(__file__, "..", "data")

orders = pl.read_csv(join(data_dir,"orders.csv"))
order_items = pl.read_csv(join(data_dir,"order_items.csv"))
customers = pl.read_csv(join(data_dir,"customers.csv"))

@app.get("/orders")
def read_orders():
    return orders.write_json()

@app.get("/order_items")
def read_order_items():
    return order_items.write_json()

@app.get("/customers")
def read_customers():
    return customers.write_json()
