from pathlib import Path
from intertable import *

# TODO: Validerer ikke .csv-filens struktur endnu
def read_csv(filename: str, data_dir: str | Path) -> list[str]:
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
    data_file = Path(data_dir, filename)
    try:
        with open(data_file, 'r', encoding="utf-8") as file:
            raw_data = file.readlines()
    except FileNotFoundError:
        print(f"FEJL: Filen '{data_file}' eksisterer ikke.")
    except Exception as err:
        print(f"FEJL: Kunne ikke læse filen '{filename}'. Følgende fejl opstod:\n    {err}")
    else:
        print(f"SUCCES: Indlæste filen '{filename}'.")
        return raw_data

def get_name(path: str | Path) -> str:
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
    return Path(path).stem

def intertable(name: str, raw_data: list[str]) -> InterTable:
    columns, *rows = raw_data

    header = {column: DataField(column, **STANDARD_FIELD) for column in columns.strip('\n').split(',')}

    data = [dict(zip(header.keys(), row.strip('\n').split(','))) for row in rows]

    return InterTable(name, Header(header), Keys(), data)

if __name__ == "__main__":
    from config import CSV
    stf = "staffs.csv"
    sts = "stores.csv"
    sta = CSV.dir / stf
    sto = CSV.dir / sts
    staffs = intertable(get_name(sta), read_csv(stf, CSV.dir))
    stores = intertable(get_name(sto), read_csv(sts, CSV.dir))
    print(staffs)
    print(stores)
