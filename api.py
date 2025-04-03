import json
import requests
import polars as pl
from db.database import Database

host, password = open("secret.txt", 'r', encoding="utf-8").readline().split(',')

# target_db = Database("root", password, "newProductDB")

def get_api_paths(host: str = "127.0.0.1", port: str = "8000") -> list[str]:
    """
    Finder paths i API'en, der har en GET-metode og returnerer dem i en liste.
    """
    try:
        # Henter API-info som JSON
        schema = requests.get(f"http://{host}:{port}/openapi.json").json()
    except Exception as err:
        print("Følgende fejl opstod:", err)
    else:
        # Hvis API'en ikke har paths, returneres en tom liste
        if (paths := schema.get("paths")) is not None:
            # Tilføjer path til liste, hvis den har en GET-metode
            return [path for path in paths if paths[path].get("get", False)]
        return []

def get_api_data(*paths: str, host: str = "127.0.0.1", port: str = "8000") -> dict[str, dict[str, dict[str, type] | list[dict[str]]]]:
    """
    Henter data fra en API ud fra en eller flere angivne paths, samt en serveradresse.

    :param paths: En eller flere paths i API'en, som data skal hentes fra.
    :param host: Adressen på API'en.
        *Påkrævet*. Standardværdi: `"127.0.0.1"`
    :type host: str
    :param port: Porten, der skal tilgås på adressen.
        *Upåkrævet*. Standardværdi: `"8000"`
    :type port: str, optional
    :return: En dict indeholdende de fundne datasæt, hver som en dict med en header- og data-del.
    :rtype: dict[str, dict[str, <u>dict[str, type]</u> | <u>list[dict[str]]</u>]]
    """
    raw_data = {}
    # Kører en request for hver path
    for path in paths:
        try:
            response = requests.get(f"http://{host}:{port}{path}")
            # Laver responsen om til en dict
            response_dict = json.loads(response.json())
            # TODO: Midlertidigt bruges polars til at finde datatyper for kolonnerne (men f.eks. datoer ses kun som str)
            table = pl.from_dicts(response_dict)
            header = table.schema.to_python()
            # target_db.create(','.join(table.columns), path[1:])
        except Exception as err:
            print("Følgende fejl opstod:", err)
        else:
            raw_data[path[1:]] = {
                "header": header,
                "data": response_dict
            }
    return raw_data

if __name__ == "__main__":
    api_paths = get_api_paths()
    # print(api_paths)
    api_data = get_api_data(*api_paths)
    print(api_data)
