import api
import csvr as csv
from db.database import Database
from intertable import *
from config import API, DB, CSV

def main() -> bool:
######################
##### EXTRACTION #####
######################

### API ###
    # De tre datasæt hentes som rådata fra API'en
    api_data = api.get_api_data(
        "/orders",
        "/order_items",
        "/customers",
        host=API.host,
        port=API.port
    )
    # Rådataene gemmes i InterTable-formatet
    orders = api.intertable("orders", api_data["orders"])
    order_items = api.intertable("order_items", api_data["order_items"])
    customers = api.intertable("customers", api_data["customers"])

### DB ###
    # Database-objekt m. forbindelse oprettes
    with Database(
        DB.username, DB.password,
        "ProductDB",
        DB.host, DB.port,
        preview=False
    ) as source_db:
        # De fire tabeller gemmes i InterTable-formatet
        brands = source_db.get_table("brands")
        categories = source_db.get_table("categories")
        products = source_db.get_table("products")
        stock = source_db.get_table("stocks", "stock")

### CSV ###
    # Rådata for de to tabeller hentes
    staff_data = csv.read_csv("staffs.csv", CSV.dir)
    store_data = csv.read_csv("stores.csv", CSV.dir)
    # Dataene gemmes i InterTable-format
    staff = csv.intertable("staff", staff_data)
    stores = csv.intertable("stores", store_data)

##########################
##### TRANSFORMATION #####
##########################

# Brands #
##########
    with brands:
        # Definerer header
        brands.header = Header({
            "brand_id": DataField("brand_id", "smallint unsigned", False, extra="auto"),
            "brand_name": DataField("brand_name", "varchar(40)", False)
        })

        # Tilføjer keys
        brands.keys.primary = "brand_id"

# Categories #
##############
    with categories:
        # Definerer header
        categories.header = Header({
            "category_id": DataField("category_id", "smallint unsigned", False, extra="auto"),
            "category_name": DataField("category_name", "varchar(40)", False)
        })

        # Tilføjer keys
        categories.keys.primary = "category_id"

# Customers #
#############
    with customers:
        # Definerer header
        customers.header = Header({
            "customer_id": DataField("customer_id", "mediumint unsigned", False, extra="auto"),
            "first_name": DataField("first_name", "varchar(40)", False),
            "last_name": DataField("last_name", "varchar(40)", False),
            "phone": DataField("phone", "char(14)"),
            "email": DataField("email", "varchar(80)", False),
            "street": DataField("street", "varchar(63)", False),
            "city": DataField("city", "varchar(40)", False),
            "state": DataField("state", "char(2)", False),
            "zip_code": DataField("zip_code", "mediumint unsigned", False),
        })

        # Tilføjer keys
        customers.keys.primary = "customer_id"
        customers.keys.unique = "email"

# Stores #
##########
    with stores:
        # Definerer header
        stores.header = Header({
            "name": DataField("name", "varchar(80)", False),
            "phone": DataField("phone", "char(14)", False),
            "email": DataField("email", "varchar(80)", False),
            "street": DataField("street", "varchar(63)", False),
            "city": DataField("city", "varchar(40)", False),
            "state": DataField("state", "char(2)", False),
            "zip_code": DataField("zip_code", "mediumint unsigned", False)
        })

        # Indsætter ny autogenereret id-kolonne i starten af tabellen
        stores << DataField("store_id", "smallint unsigned", False, extra="auto")

        # Tilføjer keys
        stores.keys.primary = "store_id"

# Staff #
#########
    with staff:
        # Definerer header
        staff.header = Header({
            "name": DataField("name", "varchar(40)", False),
            "last_name": DataField("last_name", "varchar(40)", False),
            "email": DataField("email", "varchar(80)", False),
            "phone": DataField("phone", "char(14)", False),
            "active": DataField("active", "boolean", False),
            "store_name": DataField("store_name", "text"),
            "street": DataField("street", "text"),
            "manager_id": DataField("manager_id", "smallint unsigned")
        })

        # TODO: Indbyg forbindelsen i nedenstående funktion
        store_map = {entry["name"]: entry["store_id"] for entry in stores}

        # Indsætter ny kolonne med værdier ud fra forbindelse til anden tabel
        staff @ (DataField("store_id", "smallint unsigned", False), "store_name", store_map)

        # Fjerner overflødige kolonner
        staff.remove_column("store_name", "street")

        # Indsætter ny autogenereret id-kolonne i starten af tabellen
        staff << DataField("staff_id", "smallint unsigned", False, extra="auto")

        # Tilføjer keys
        staff.keys.primary = "staff_id"
        staff.keys.foreign = {
            "store_id": ("stores", "store_id"),
            "manager_id": ("staff", "staff_id")
        }
        staff.keys.unique = ["email", "phone"]

        # Retter forkert 'manager_id' for to medarbejdere
        staff[8]["manager_id"] = 8
        staff[9]["manager_id"] = 8

# Orders #
##########
    with orders:
        # Definerer header
        orders.header = Header({
            "order_id": DataField("order_id", "mediumint unsigned", False, extra="auto"),
            "customer_id": DataField("customer_id", "mediumint unsigned", False),
            "order_status": DataField("order_status", "tinyint unsigned", False),
            "order_date": DataField("order_date", "date", False),
            "required_date": DataField("required_date", "date", False),
            "shipped_date": DataField("shipped_date", "date"),
            "store": DataField("store", "text"),
            "staff_name": DataField("staff_name", "text")
        })

        # TODO: Indbyg forbindelsen i nedenstående funktion
        staff_map = {entry["name"]: entry["staff_id"] for entry in staff}

        # Indsætter ny kolonne med værdier ud fra forbindelse til anden tabel
        orders @ (DataField("store_id", "smallint unsigned", False), "store", store_map)
        orders @ (DataField("staff_id", "smallint unsigned", False), "staff_name", staff_map)

        # Fjerner overflødige kolonner
        orders.remove_column("store", "staff_name")

        # Tilføjer keys
        orders.keys.primary = "order_id"
        orders.keys.foreign = {
            "customer_id": ("customers", "customer_id"),
            "store_id": ("stores", "store_id"),
            "staff_id": ("staff", "staff_id")
        }

    # COUNT() = len();  WHERE = if; FROM = for in
    # SELECT COUNT(shipped_date) FROM orders WHERE shipped_date IS NULL
    # print(len([nulldate for nulldate in orders["shipped_date"].values() if nulldate is None]))

# Products #
############
    with products:
        # Definerer header
        products.header = Header({
            "product_id": DataField("product_id", "mediumint unsigned", False, extra="auto"),
            "product_name": DataField("product_name", "varchar(80)", False),
            "brand_id": DataField("brand_id", "smallint unsigned", False),
            "category_id": DataField("category_id", "smallint unsigned", False),
            "model_year": DataField("model_year", "year", False),
            "list_price": DataField("list_price", "decimal(10,2)", False)
        })

        # Tilføjer keys
        products.keys.primary = "product_id"
        products.keys.foreign = {
            "brand_id": ("brands", "brand_id"),
            "category_id": ("categories", "category_id")
        }
        # products.keys.unique = "product_name"

# Order Items #
###############
    with order_items:
        # Definerer header
        order_items.header = Header({
            "order_id": DataField("order_id", "mediumint unsigned", False),
            "item_id": DataField("item_id", "tinyint unsigned", False),
            "product_id": DataField("product_id", "mediumint unsigned", False),
            "quantity": DataField("quantity", "smallint unsigned", False),
            "list_price": DataField("list_price", "decimal(10,2)", False),
            "discount": DataField("discount", "decimal(3,2)", False, default=Decimal(0.00)),
        })

        # Tilføjer keys
        order_items.keys.primary = ["order_id", "item_id"]
        order_items.keys.foreign = {
            "order_id": ("orders", "order_id"),
            "product_id": ("products", "product_id")
        }

# Stock #
#########
    with stock:
        # Definerer header
        stock.header = Header({
            "store_name": DataField("store_name", "text"),
            "product_id": DataField("product_id", "mediumint unsigned", False),
            "quantity": DataField("quantity", "mediumint unsigned", False)
        })

        # Indsætter ny kolonne med værdier ud fra forbindelse til anden tabel
        stock @ (DataField("store_id", "smallint unsigned", False), "store_name", store_map)

        # Fjerner overflødig kolonne
        del stock["store_name"]

        # Tilføjer keys
        stock.keys.primary = ["store_id", "product_id"]
        stock.keys.foreign = {
            "product_id": ("products", "product_id")
        }

# Størrelsen af tabellerne efter transformation
    all_tables = (orders, order_items, customers, brands, categories, products, stock, staff, stores)
    transform_sizes = {table.name: table.size for table in all_tables}
    print(transform_sizes)

###################
##### LOADING #####
###################
    # Grupperer tabellerne efter antal foreign key-led
    zero_fk: tuple[InterTable] = (brands, categories, customers, stores)
    one_fk: tuple[InterTable] = (staff,)
    two_fk: tuple[InterTable] = (orders, products)
    three_fk: tuple[InterTable] = (order_items, stock)

    load_tuple: tuple[InterTable] = (*zero_fk, *one_fk, *two_fk, *three_fk)

    # Opretter et nyt database-objekt
    with Database(
        DB.username, DB.password,
        "bikecorpdb",
        DB.host, DB.port,
        preview=False,
        init_load=load_tuple
    ) as target_db:
        print(target_db.info())

    return True

if __name__ == "__main__":
    if main():
        msg = "SUCCES: Alle data hentet og indsat i ny database."
        print('=' * len(msg))
        print(msg)
        print('=' * len(msg))
