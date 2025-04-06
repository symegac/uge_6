from db.database import Database
from config import *

# Forbinder til MySQL-database
db = Database(DB.username, DB.password, DB.database, DB.host, DB.port, preview=False)

### Den oprindelige proces ###
def slow_to_write() -> None:
    # Navn
    prod = {"name": "products"}
    # Header
    prod_info = db.info("products")
    prod["header"] = {}
    for info in prod_info:
        prod["header"][info[0]] = {
            "type": info[1],
            "nullable": info[2],
            "key": info[3],
            "default": info[4],
            "extra": info[5]
        }
    # Keys
    prod["keys"] = {}
    key_info = db.read("INFORMATION_SCHEMA.KEY_COLUMN_USAGE", eq=("CONSTRAINT_SCHEMA", db.database), eq2=("TABLE_NAME", "products"))
    prod["keys"]["primary"] = [key["COLUMN_NAME"] for key in key_info if key["CONSTRAINT_NAME"] == "PRIMARY"]
    prod["keys"]["foreign"] = {key["COLUMN_NAME"]: (key["REFERENCED_TABLE_NAME"], key["REFERENCED_COLUMN_NAME"],) for key in key_info if key["REFERENCED_TABLE_NAME"] is not None}
    prod["keys"]["unique"] = [info[0] for info in prod_info if info[3] == "UNI"]
    # Data
    prod["data"] = db.read("products")

    return prod

#######################################################################
### Semimanuelt udtræk af de forskellige dele med de nye funktioner ###
def four_lines() -> None:                                           ###
    prods = {"name": "products"}                                    ###
    prods["header"] = db.get_header("products")                     ###
    prods["keys"] = db.get_keys("products")                         ###
    prods["data"] = db.read("products")                             ###
                                                                    ###
    return prods                                                    ###

#######################################################################
### Fuld proces i en funktion                                       ###
def one_line() -> None:                                             ###
    products = db.get_table("products")                             ###
                                                                    ###
    return products                                                 ###

# >>> one_line()
# {'name': 'products', 'header': {'product_id': {'type': 'int', 'nullable': False,
# 'default': None, 'extra': 'auto_increment'}, 'product_name': {'type': 'varchar(255)',
# 'nullable': False, 'default': None, 'extra': ''}, 'brand_id': {'type': 'int',
# 'nullable': True, 'default': None, 'extra': ''}, 'category_id': {'type': 'int',
# 'nullable': True, 'default': None, 'extra': ''}, 'model_year': {'type': 'int',
# 'nullable': True, 'default': None, 'extra': ''}, 'list_price': {'type': 'float',
# 'nullable': True, 'default': None, 'extra': ''}}, 'keys': {'primary': 'product_id',
# 'foreign': {'brand_id': ('brands', 'brand_id'), 'category_id': ('categories', 'category_id')}},
# 'data': [{'product_id': 1, 'product_name': 'Trek 820 - 2016', 'brand_id': 9, 'category_id': 6,
# 'model_year': 2016, 'list_price': 379.99}, {'product_id': 2, 'product_name':
# 'Ritchey Timberwolf Frameset - 2016', 'brand_id': 5, 'category_id': 6, 'model_year': 2016,
# 'list_price': 749.99}, {'product_id': 3, 'product_name': 'Surly Wednesday Frameset - 2016',
# 'brand_id': 8, 'category_id': 6, 'model_year': 2016, 'list_price': 999.99}, {'product_id': 4,
# 'product_name': 'Trek Fuel EX 8 29 - 2016', 'brand_id': 9, 'category_id': 6, 'model_year': 2016,
# 'list_price': 2899.99}, {'product_id': 5, 'product_name': 'Heller Shagamaw Frame - 2016',
# 'brand_id': 3, 'category_id': 6, 'model_year': 2016, 'list_price': 1320.99}, {'product_id': 6,
# 'product_name': 'Surly Ice Cream Truck Frameset - 2016', 'brand_id': 8, 'category_id': 6,
# 'model_year': 2016, 'list_price': 469.99}, {'product_id': 7, 'product_name': 'Trek Slash 8 27.5 - 2016',
# 'brand_id': 9, 'category_id': 6, 'model_year': 2016, 'list_price': 3999.99}, {'product_id': 8,
# 'product_name': 'Trek Remedy 29 Carbon Frameset - 2016', 'brand_id': 9, 'category_id': 6,
# 'model_year': 2016, 'list_price': 1799.99}, {'product_id': 9, 'product_name': 'Trek Conduit+ - 2016',
# 'brand_id': 9, 'category_id': 5, 'model_year': 2016, 'list_price': 2999.99}, {'product_id': 10,
# 'product_name': 'Surly Straggler - 2016', 'brand_id': 8, 'category_id': 4, 'model_year': 2016,
# 'list_price': 1549.0}, {'product_id': 11, 'product_name': 'Surly Straggler 650b - 2016',
# 'brand_id': 8, 'category_id': 4, 'model_year': 2016, 'list_price': 1680.99}, {'product_id': 12,
# 'product_name': 'Electra Townie Original 21D - 2016', 'brand_id': 1, 'category_id': 3,
# 'model_year': 2016, 'list_price': 549.99}, {'product_id': 13, 'product_name':
# 'Electra Cruiser 1 (24-Inch) - 2016', 'brand_id': 1, 'category_id': 3, 'model_year': 2016,
# 'list_price': 269.99}, {'product_id': 14, 'product_name': "Electra Girl's Hawaii 1 (16-inch) - 2015/2016",
# 'brand_id': 1, 'category_id': 3, 'model_year': 2016, 'list_price': 269.99}, {'product_id': 15,
# 'product_name': 'Electra Moto 1 - 2016', 'brand_id': 1, 'category_id': 3, 'model_year': 2016,
# 'list_price': 529.99}, {'product_id': 16, 'product_name': 'Electra Townie Original 7D EQ - 2016', 'brand_id': 
#   ... etc. ...

#######################################################################
### Kører resten                                                    ###
def three_at_once() -> None:                                        ###
    brands = db.get_table("brands")                                 ###
    categories = db.get_table("categories")                         ###
    stock = db.get_table("stocks")                                  ###
                                                                    ###
    print(brands)                                                   ###
    print(categories)                                               ###
    print(stock)                                                    ###



if __name__ == "__main__":
    input(slow_to_write())
    input(four_lines())
    input(one_line())
    three_at_once()
