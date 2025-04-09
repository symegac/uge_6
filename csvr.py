import os.path
from intertable import *

# TODO: Validerer ikke .csv-filens struktur endnu
def read_csv(filename: str, data_dir: str = "data") -> list[str]:
    """
    Indlæser en *.csv*-fil og omdanner den til rådata, der kan behandles.

    :param filename: Filnavnet på filen, der skal indlæses.
        *Påkrævet*.
    :type filename: str
    :param data_dir: Mappen/kataloget, hvori .csv-filen er placeret.
        *Påkrævet*. Standardværdi: ``"data"``
    :type data_dir: str

    :return: Den indlæste fil med hver række som en tekststreng i en liste.
    :rtype: list[str]
    """
    data_file = os.path.join(data_dir, filename)
    try:
        with open(data_file, 'r', encoding="utf-8") as file:
            raw_data = file.readlines()
    except FileNotFoundError:
        print(f"FEJL: Filen '{data_file}' eksisterer ikke.")
    except Exception as err:
        print(f"FEJL: Kunne ikke læse filen '{filename}'. Følgende fejl opstod:\n    ", err)
    else:
        print(f"SUCCES: Indlæste filen '{filename}'.")
        return raw_data

def get_name(path: str) -> str:
    """
    Finder navnet på en tabel ud fra navnet på den angivne fil.

    Burde virke på *.csv*, *.txt*, *.xlsx* og alle andre filtyper,
    så længe filen har det navn, som tabellen skal have.

    :param path: Placeringen af datafilen,
        enten absolut eller relativ (ift. denne fil).
        *Påkrævet*.
    :type path: str

    :return: Navnet på tabellen, baseret på filens navn.
    :rtype: str
    """
    return os.path.splitext(os.path.basename(path))[0]

def csv_to_intertable(name: str, raw_data: list[str]) -> InterTable:
    columns, *rows = raw_data

    header = {column: STANDARD_FIELD for column in columns.strip('\n').split(',')}

    data = [dict(zip(header.keys(), row.strip('\n').split(','))) for row in rows]

    return InterTable(name, header, Keys(), data)

if __name__ == "__main__":
    import os.path
    sta = os.path.join("data_csv", "staffs.csv")
    sto = os.path.join("data_csv", "stores.csv")
    staffs = csv_to_intertable(get_name(sta), read_csv("staffs.csv", "data_csv"))
    stores = csv_to_intertable(get_name(sto), read_csv("stores.csv", "data_csv"))
    print(staffs)
    print(stores)
