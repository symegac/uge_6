import json
import requests
import typing
from intertable import *

def get_api_paths(host: str = "127.0.0.1", port: str = "8000") -> list[str]:
    """
    Finder paths i API'en, der har en GET-metode og returnerer dem i en liste.
    """
    try:
        # Henter API-info som JSON
        schema: dict[str, dict[str, dict]] = requests.get(f"http://{host}:{port}/openapi.json").json()
    except Exception as err:
        print("Følgende fejl opstod:", err)
    else:
        # Hvis API'en ikke har paths, returneres en tom liste
        if (paths := schema.get("paths")) is not None:
            # Tilføjer path til liste, hvis den har en GET-metode
            return [path for path in paths if paths[path].get("get", False)]
        return []

def get_api_data(*paths: str, host: str = "127.0.0.1", port: str = "8000") -> dict[str, list[dict[str, typing.Any]]] | list[dict[str, typing.Any]]:
    """
    Henter data fra en API ud fra en eller flere angivne paths, samt en serveradresse.

    :param paths: En eller flere paths i API'en, som data skal hentes fra.
    :param host: Adressen på API'en.
        *Påkrævet*. Standardværdi: `"127.0.0.1"`
    :type host: str
    :param port: Porten, der skal tilgås på adressen.
        *Upåkrævet*. Standardværdi: `"8000"`
    :type port: str, optional
    :return: En dict indeholdende de fundne datasæt, hver som en liste med en header- og data-del.
        Eller blot et enkelt datasæt.
    :rtype: dict[str, list[dict[str, typing.Any]]] | list[dict[str, typing.Any]]
    """
    raw_data = {}
    # Kører en request for hver path
    for path in paths:
        try:
            response = requests.get(f"http://{host}:{port}{path}")
            # Laver responsen om til en dict
            response_dict = json.loads(response.json())
        except Exception as err:
            print("FEJL: Følgende fejl opstod:", err)
        else:
            print(f"SUCCES: Hentede data fra API'en ved path '{path}'")
            raw_data[path[1:]] = response_dict
    return raw_data if len(paths) != 1 else raw_data[paths[0][1:]]

def get_columns(row: dict[str, typing.Any] | list[dict[str, typing.Any]]) -> tuple[str]:
    if isinstance(row, list):
        row = row[0]
    return row.keys()

def intertable(name: str, data: list[dict[str, typing.Any]]) -> InterTable:
    header = {column: DataField(column, **STANDARD_FIELD) for column in get_columns(data)}

    return InterTable(name, Header(header), Keys(), data)

if __name__ == "__main__":
    from config import API
    api_data = get_api_data(
        "/orders",
        "/order_items",
        "/customers",
        host=API.localhost,
        port=API.port
    )
    orders = intertable("orders", api_data["orders"])
    order_items = intertable("order_items", api_data["order_items"])
    customers = intertable("customers", api_data["customers"])

    print(orders.keys, orders.header, order_items.keys, customers.keys)
    print(orders)
