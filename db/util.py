import os.path

# Ændr dette, hvis projektet skal laves om til et modul, der kan importeres
data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

# TODO: Validerer ikke .csv-filens struktur endnu
def read_csv(filename: str, data_dir: str = data_dir) -> list[str]:
    """
    Indlæser en *.csv*-fil og omdanner den til rådata, der kan behandles.

    :param filename: Filnavnet på filen, der skal indlæses.
        *Påkrævet*.
    :type filename: str
    :param data_dir: Mappen/kataloget, hvori .csv-filen er placeret.
        *Påkrævet*. Standardværdi: ``data_dir``
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

def main() -> None:
    pass

if __name__ == "__main__":
    main()
