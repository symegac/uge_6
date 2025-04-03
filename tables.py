import os
import os.path
import requests
import polars as pl
from db.database import Database
from db import util

host, password = open("secret.txt", 'r', encoding="utf-8").readline().split(',')
all_tables = []

# Finder info om de forskellige paths, der findes i API'en (hvis man nu antager, at vi ikke kender alle de forskellige datasæt, der ligger der)
api_response = requests.get(f"http://{host}:8000/openapi.json").json()
# Tager tabelnavne fra paths (fjerner '/')
api_tables = [table[1:] for table in api_response["paths"]]
input(api_tables)

# Forbinder til database
source_db = Database("root", password, "ProductDB", host=host, port="3306")
# Finder info om tabeller i databasen
db_tables = [table[0] for table in source_db.info()]
input(db_tables)

# Finder alt i 'data_csv'-mappen
filelist = os.listdir("data_csv")
# Tager navnet, hvis det er en fil og filtypeformatet er '.csv'
csv_tables = [util.get_name(file) for file in filelist if os.path.isfile(os.path.join("data_csv", file)) and file.endswith(".csv")]
input(csv_tables)

# Sorterer tabelnavne alfabetisk
all_tables = sorted([*api_tables, *db_tables, *csv_tables], key=lambda x: x)
print(all_tables)