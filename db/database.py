import getpass
import typing
import datetime
import decimal
from . import util
from . import connector
from intertable import *

class Database(connector.DatabaseConnector):
    """
    Et objekt, der er forbundet til en MySQL-instans og som regel en database heri,
    og som kan interagere med databasen og tabellerne, som den indeholder.

    :param username: Brugernavnet, der skal bruges til at logge ind med.
        *Påkrævet*. Standardværdi: ``''``
    :type username: str
    :param password: Adgangskoden, der skal bruges til at logge ind med.
        *Påkrævet*. Standardværdi: ``''``
    :type password: str
    :param database: Navnet på databasen, der evt. skal forbindes til.
        *Upåkrævet*. Standardværdi: ``''``
    :type database: str
    :param host: Adressen på serveren, der forbindes til.
        Hvis tom, bruges MySQL-standarden ``"127.0.0.1"``.
        *Upåkrævet*. Standardværdi: ``''``
    :type host: str
    :param port: Porten, der forbindes til.
        Hvis tom, bruges MySQL-standarden ``"3306"``.
        *Upåkrævet*. Standardværdi: ``''``
    :type port: str
    :param init_load: En liste over datafiler, der ved initialisering automatisk skal
        indlæses som tabeller i databasen.
        *Upåkrævet*. Standardværdi: ``[]``
    :type init_load: list[str]
    :param preview: Bestemmer, om queries skal forhåndsvises inden eksekvering.
        *Upåkrævet*. Standardværdi: ``True``
    :type preview: bool
    """
    def __init__(self,
        username: str = '',
        password: str = '',
        database: str = '',
        host: str = '',
        port: str = '',
        init_load: list[str] = [],
        preview: bool = True,
    ) -> None:
        """
        Konstruktøren af database-objektet.

        :param username: Brugernavnet, der skal bruges til at logge ind med.
            *Påkrævet*. Standardværdi: ``''``
        :type username: str
        :param password: Adgangskoden, der skal bruges til at logge ind med.
            *Påkrævet*. Standardværdi: ``''``
        :type password: str
        :param database: Navnet på databasen, der evt. skal forbindes til.
            *Upåkrævet*. Standardværdi: ``''``
        :type database: str
        :param host: Adressen på serveren, der forbindes til.
            Hvis tom, bruges MySQL-standarden ``"127.0.0.1"``.
            *Upåkrævet*. Standardværdi: ``''``
        :type host: str
        :param port: Porten, der forbindes til.
            Hvis tom, bruges MySQL-standarden ``"3306"``.
            *Upåkrævet*. Standardværdi: ``''``
        :type port: str
        :param init_load: En liste over datafiler, der ved initialisering automatisk skal
            indlæses som tabeller i databasen.
            *Upåkrævet*. Standardværdi: ``[]``
        :type init_load: list[str]
        :param preview: Bestemmer, om queries skal forhåndsvises inden eksekvering.
            *Upåkrævet*. Standardværdi: ``True``
        :type preview: bool
        """
        # Konfiguration
        self.preview = preview
        # Initialiserer connectoren
        super().__init__(username, password, database, host, port)

        if self.database:
            # Hvis forbindelsen ikke kan skabes (f.eks. fordi det angivne databasenavn ikke eksisterer),
            # kan brugeren forsøge at oprette en database med navnet
            if not self.connection:
                new = input(f"Vil du forsøge at oprette en ny database med navnet '{self.database}'? (j/N): ")
                if new.lower() in ['j', 'y']:
                    self.create_database(self.database)
                    # Skal logge ind igen for at forny forbindelserne
                    self._full_login(getpass.getpass("Indtast adgangskode igen: "))
            # Loader tabeller til databasen fra start, hvis nogen oplyses
            elif init_load:
                self.load(*init_load)

    def _execute(self,
        query: str,
        params: Parameter | list[Parameter] = {},
        /, *,
        db: bool = True,
        read: bool = False,
        select: bool = False
    ) -> bool | list[tuple]:
        """
        Eksekverer et SQL-query.

        Hvis flere query-parametergrupper ('params') sendes med i en liste, gentages queriet for hver af disse.

        :param query: Queriet, der skal eksekveres. Skal skrives i SQL.
            *Påkrævet*.
        :type query: str
        :param params: En dict eller liste af dicts indeholdende parameteriserede værdier
            bestemt af brugeren, der skal indsættes sikkert i queriet,
            bl.a. for at undgå SQL injection.
            *Upåkrævet*. Standardværdi: ``{}``
        :type params: dict[str, Any] | list[dict[str, Any]]
        :param db: Bestemmer om handlingen udføres i en specifik database eller direkte.
            Skal være ``False`` ved f.eks. oprettelse af ny database eller nulstilning af database.
            *Påkrævet*. Standardværdi: ``True``
        :type db: bool
        :param read: Bestemmer, om der skal bruges en buffered cursor,
            så data kan læses og fetches fra databasen.
            *Upåkrævet*. Standardværdi: ``False``
        :type read: bool

        :return: Queriet kunne eksekveres, og handlingen blev gennemført.
        :rtype: bool: ``True``
        :return: Handlingen kunne ikke gennemføres.
        :rtype: bool: ``False``
        :return: Den læste data fra databasen, hvis en READ-operation kunne gennemføres.
        :rtype: list[tuple]
        """
        connection = self.connection if db else self.direct_connection
        if not connection:
            self._error(f"Kan ikke udføre nogen handlinger uden en forbindelse til {"databasen" if db else "serveren"}.")
            quit()

        try:
            with connection.cursor(buffered=read, dictionary=select) as cursor:
                # Hvis 'params' er en liste, køres queriet for hver gruppe 'params'
                if isinstance(params, list):
                    cursor.executemany(query, params)
                # Ellers køres queriet kun én gang
                else:
                    cursor.execute(query, params)
            # Committer evt. ændringer i tabeller eller data
            connection.commit()
            # .__exit__() er implementeret for cursoren i mysql.connector,
            # så denne behøves ikke lukkes manuelt, når with-blokke bruges

            # Hvis i læsetilstand, returneres den læste data
            if read:
                return cursor.fetchall()
        except Exception as err:
            self._error("Kunne ikke eksekvere queriet.", err)
            force = input("Fortsæt kørsel af programmet alligevel? (j/N): ")
            if force.lower() in ['j', 'y']:
                return False
            quit()
        else:
            return True

    def _preview(self, query: str) -> None:
        """
        Viser et preview at queriet, der skal til at køres.

        For at fortsætte eksekveringen, skal brugeren trykke på Enter.

        :param query: Queriet, der skal til at køres.
            *Påkrævet*.
        :type query: str
        """
        if self.preview:
            msg = " > " + query
            title = "Forhåndsvisning af forespørgsel:"
            print('-' * max(len(msg), len(title)))
            print(title)
            input(msg)
            print('-' * max(len(msg), len(title)))

    def _format_column(self, column_name: str) -> str:
        """
        Formaterer en reference til en kolonne korrekt med backticks.

        Hvis referencen indeholder et punktum, f.eks. hvis kolonner fra flere tabeller indgår i et query,
        sættes backticks rundt om hver enkelt del af kolonnenavnet.

        :param column_name: Kolonnenavnet/-referencen, der skal formateres.
            *Påkrævet*.
        :type column_name: str
        :return: Den formaterede kolonnereference.
        :rtype: str
        """
        column_parts = []
        # Opdeler navn med flere dele
        split_column = column_name.split('.') if '.' in column_name else [column_name]
        # Sætter backticks omkring hver enkelt del
        for column_part in split_column:
            column_parts.append(f"`{column_part}`")
        # Returnerede den samlede reference
        return '.'.join(column_parts)

    # CREATE-operationer
    def create_database(self, database_name: str) -> None:
        """
        Opretter en database med det angivne navn.

        :param database_name: Navnet på databasen, der ønskes oprettet.
            *Påkrævet*.
        :type database_name: str
        """
        database_query = f"CREATE DATABASE `{database_name}`"

        self._preview(database_query)

        # Hvis eksekveringen gennemføres, vises besked
        if self._execute(database_query, db=False):
            print(f"SUCCES: Databasen '{database_name}' blev oprettet.")

    def create(self,
        columns: list[DataField],
        table_name: TableName,
        # keys: Keys = {},
    ) -> None:
        """
        Opretter en ny tabel ud fra de angivne oplysninger.

        :param columns: _description_
        :type columns: str
        :param table_name: _description_, defaults to "table"
        :type table_name: str, optional
        :param primary_key: _description_, defaults to ''
        :type primary_key: str, optional
        :param foreign_key: _description_, defaults to {}
        :type foreign_key: dict, optional
        """
        create_query = f"CREATE TABLE `{table_name}` ("
        
        column_queries = []

        for column in columns:
            column_query = f"`{column.name}` {column.datatype}"
            if not column.nullable:
                column_query += " NOT NULL"
            if column.default is not None:
                column_query += f" DEFAULT {column.default}"
            if column.extra:
                column_query += ' ' + column.extra
            column_queries.append(column_query)
            # if "id" in column:
            #     create_query += "INTEGER NOT NULL"
            # elif "name" in column:
            #     create_query += "VARCHAR(80) NOT NULL"
            # elif "email" in column:
            #     create_query += "VARCHAR(254) NOT NULL"
            # elif "price" in column:
            #     # For dette datasæt er (P=8,D=5) i DECIMAL(P,D)
            #     # Men for pengebeløb burde D vel egentlig være 2
            #     create_query += "DECIMAL(10,5) NOT NULL"
            # elif "date" in column:
            #     create_query += "DATETIME NOT NULL"
            # elif column in ["customer", "product", "quantity", "zip_code", "order_status"]:
            #     create_query += "INTEGER NOT NULL"
            # elif "discount" in column:
            #     create_query += "DECIMAL(3,2) NOT NULL"
            # else:
            #     create_query += "VARCHAR(80) NOT NULL"
        create_query += ", ".join(column_queries) + ')'

        self._preview(create_query)

        if self._execute(create_query):
            print(f"SUCCES: Oprettede tabellen '{table_name}'.")

        # if primary_key:
        #     self.primary_key(table_name, primary_key)
        #     self.add_key(table_name, unique_key)
        # if foreign_key:
        #     self.foreign_key(table_name, foreign_key)
        #     # self.add_key(table_name, foreign_key)
        # if unique_key:
        #     self.add_key(table_name, unique_key)

    # TODO: Forsøg at matche kolonnenavne fra dataens header med kolonnenavne fra den valgte tabel
    # TODO: Implementér et system til at skippe eller overwrite, hvis et felt i en række i datasættet
    # har samme værdi som ditto i tabellen. Hvis altså kolonnen har PRIMARY KEY eller UNIQUE som constraint.
    def insert(self,
        data: list[str], # TableData
        table_name: TableName,
        header: bool = True
        # header: TableHeader
    ) -> None:
        """
        Indsætter en eller flere rækker data i en tabel.

        :param data: Dataene, der ønskes indsat i tabellen.
            *Påkrævet*.
        :type data: list[str]
        :param table_name: Navnet på tabellen, som dataen skal indsættes i.
            *Påkrævet*.
        :type table_name: str
        :param header: Angiver, om datasættet, der inputtes, indeholder en header med kolonnenavne,
            som skal springes over.
            Hvis ``True`` forsøges dataen desuden at matches med den angivne tabels kolonnenavne.
            *Upåkrævet*. Standardværdi: ``True``
        :type header: bool

        :return: Hvis tabellen ikke findes, eller hvis dataene ikke har samme antal kolonner som tabellen.
        :rtype: None
        """
        # Benyttes ikke endnu, men kan bruges til at bytte rundt på kolonner,
        # hvis de står i en anden rækkefølge end tabellen, som dataene skal indsættes i
        if header:
            columns = data[0].strip('\n').split(',')
        # Springer over header
        rows = data[1:] if header else data
        # Opdeler hver række i felter
        rows = [row.strip('\n').split(',') for row in rows]

        # Henter info om tabellen
        if not (table_info := self.info(table_name)):
            return
        # Tjekker om alle rækker i den inputtede dataliste har samme antal felter, som der er kolonner i den angivne tabel,
        # dvs. om længden af hver række (list[str]) er den samme som længden af headerinfoen (list[tuple])
        if not all(len(row) == len(table_info) for row in iter(rows)):
            self._error("En eller flere rækker data er uforenelig med tabellens format.")
            return

        # Danner query
        insert_query = f"INSERT INTO `{table_name}` ("
        # Kolonnenavne (med backticks, fordi navnene er taget fra tabellen)
        insert_query += ", ".join([f"`{column[0]}`" for column in table_info]) + ") VALUES ("
        # Kolonneværdier (med %()s, fordi det er værdier oplyst af brugeren, der skal tjekkes)
        insert_query += ", ".join([f"%({column[0]})s" for column in table_info]) + ')'

        # Danner dict over parametre til indsættelse af data
        insert_params = []
        for row in rows:
            # Konverterer str til passende datatype
            # Koverteringen lader til at være spild af tid,
            # da værdiene også omdannes til de rette typer,
            # hvis man bare indsætter tekst...
            # for index, column in enumerate(table_info):
                # insert_param[column[0]] = row[index]
                # Kun de to første værdier (navn og type) tages fra kolonneinfoen
                # column_name, column_type, *_ = column
                # if "int" in column_type:
                #     value = int(row[index])
                # elif "datetime" in column_type:
                #     value = datetime.datetime.fromisoformat(row[index])
                # # Dækker char, varchar, text og [adj.]text
                # elif "char" in column_type or "text" in column_type:
                #     value = row[index]
                # elif "float" in column_type:
                #     value = float(row[index])
                # elif "decimal" in column_type:
                #     value = decimal.Decimal(row[index])
                # insert_param[column_name] = value
            # Ny, forenklet måde
            insert_param = {column[0]: row[index] for index, column in enumerate(table_info)}
            insert_params.append(insert_param)

        self._preview(insert_query)

        if self._execute(insert_query, insert_params):
            print(f"SUCCES: Data indsat i tabellen '{table_name}'.")

    def new_table(self,
            data: list[str], # TableData
            table_name: TableName = "table",
            header: str = '' # TableHeader
        ) -> None:
        """
        Opretter en ny tabel og indsætter data i den.

        Svarer til at bruge ``.create()`` efterfulgt af ``.insert()``.

        :param data: Dataene, der danner grundlag for den nye tabel.
            *Påkrævet*.
        :type data: list[str]
        :param table_name: Navnet på tabellen, der ønskes oprettet.
            *Påkrævet*. Standardværdi: ``"table"``
        :type table_name: str
        :param header: En kommasepareret tekststreng indeholdende kolonnenavne.
            *Upåkrævet*. Standardværdi: ``''``
        :type header: str
        """
        if not header:
            header, *body = data
        self.create(header, table_name)
        self.insert(body, table_name, header=False)

    def load(self, *tables: str) -> None:
        """
        Indlæser data fra de(n) angivne fil(er) og opretter en tabel i databasen for hver af dem.

        :param tables: En eller flere filer, der skal laves en tabel af.
        :type tables: str
        """
        for table in tables:
            raw_data = util.read_csv(table)
            table_name = util.get_name(table)
            self.new_table(raw_data, table_name)

    # READ-operationer
    # TODO: Tilføj en måde, hvorpå foreign keys kan bruges til at joine eller læse data fra andre tabeller
    def read(self,
        table_name: TableName,
        *column_name: ColumnName,
        joins: list[dict[str, TableName | ColumnName]] = [],
        order: int | ColumnName = 0,
        direction: str = 'a',
        limit: int = 0,
        offset: int = 0,
        **kwargs
    ) -> TableData | None:
        """
        Læser data fra en tabel.

        :param table_name: Navnet på den tabel, som data skal læses fra.
            *Påkrævet*.
        :type table_name: str
        :param column_name: Navnet eller navnene på den kolonne eller de kolonner, som data skal læses fra.
            *Upåkrævet*.
        :type column_name: str
        :param joins: En liste med en dict indeholdende parametrene for hvert join, der skal indsættes i queriet.
            Et join har som regel formen ``{
                "right": tabel_2,
                "on_left": kolonne_1,
                "on_right": kolonne_2.
                "join_type": JOIN-type
            }`` i brug, men parameteren ``"left"`` kan også oplyses om nødvendigt.
            *Upåkrævet*. Standardværdi: ``[]``
        :type joins: list[dict[str, str]]
        :param order: Kolonnen, som resultatet ordnes efter.
            Enten *int*, der vælger indekset af kolonnen blandt de valgte kolonner,
            eller *str*, der vælger ud fra navnet på kolonnen.
            *Upåkrævet*. Standardværdi: ``0``
        :type order: int | str
        :param direction: Angiver hvilken retning, resultatet skal ordnes i.
            ``'a'``, ``"asc"`` eller ``"ascending"`` er opadgående rækkefølge, mens
            ``'d'``, ``"desc"`` eller ``"descending"`` er nedadgående rækkefølge.
            *Upåkrævet*. Standardværdi: ``'a'``
        :type direction: str
        :param limit: Mængden af rækker, der skal læses.
            Når værdien er ``0``, læses alle resultater.
            *Upåkrævet*. Standardværdi: ``0``
        :type limit: int
        :param offset: Mængden af rækker, der springes over, inden læsningen påbegyndes.
            Når værdien er ``0``, læses alle resultater.
            *Upåkrævet*. Standardværdi: ``0``
        :type offset: int

        :return: En liste med rækker indeholdende data fra de(n) valgte kolonne(r).
        :rtype: list[dict[str, Any]]
        :return: Hvis READ-operationen ikke kunne gennemføres.
        :rtype: None
        """
        select_params = {}

        select_query = "SELECT "
        # Hvis antallet af kolonner angivet er > 0,
        # vælges kun de angivne kolonner
        if column_name:
            columns = []
            for column in column_name:
                columns.append(self._format_column(column))
            select_query += ", ".join(columns)
        # Ellers vælges alle kolonner
        else:
            select_query += '*'
        select_query += f" FROM {self._format_column(table_name)}"

        # Tilføjer join(s)
        if joins:
            for join in joins:
                select_query += self._join(left=table_name, **join)

        # Tilføjer where-constraints
        if kwargs:
            where_query, where_params = self._where(**kwargs)
            select_query += where_query
            select_params.update(where_params)

        # Tilføjer sorteringsretning
        # quickfix: (sættes nu altid på queriet, da joins sorteres efter nyligst joinede tabel?)
        select_query += self._sort(column_name, order, direction)

        # Tilføjer limit og offset
        if limit or offset:
            limit_query, limit_params = self._limit(limit, offset)
            select_query += limit_query
            select_params.update(limit_params)

        self._preview(select_query)

        result = self._execute(select_query, select_params, read=True, select=True)
        if result:
            print(f"SUCCES: Dataene blev læst fra '{table_name}'.")
            return result

    def _where(self, **kwargs):
        # TODO: Tilføj OR osv.?
        where_queries = []
        where_params = {}
        # For hver kwarg ses det, om det er et WHERE keyword
        for key, value in kwargs.items():
            kwarg_query, kwarg_params = self._where_type(key, value, len(where_queries))
            # Hvis ja, opbevares de resulterende query-dele og parametre
            if kwarg_query:
                where_queries.append(kwarg_query)
            if kwarg_params:
                where_params.update(kwarg_params)

        # Hvis der både er query-dele og parametre, genereres queriet, og parametrene tilføjes
        if where_queries and where_params:
            where_query = " WHERE"
            # Hvis der er mere end 1 query-del, sættes de sammen med AND
            if len(where_queries) > 1:
                where_query += " AND".join(where_queries)
            else:
                where_query += f" {where_queries[0]}"
            return where_query, where_params

    def _where_type(self, key: str, value: tuple, where_count: int) -> tuple[str, dict]:
        kwarg_query = f" `{value[0]}`"
        kwarg_params = {}
        # WHERE column_name LIKE val
        if key.lower().startswith(("like", "lk")):
            name = f"like_{where_count}"
            kwarg_query += " LIKE %(" + name + ")s"
            kwarg_params.update({name: value[1]})
        # WHERE column_name = val
        elif key.lower().startswith("eq"):
            name = f"equals_{where_count}"
            kwarg_query += " = %("+ name + ")s"
            kwarg_params.update({name: value[1]})
        # WHERE column_name BETWEEN val_low AND val_high
        elif key.lower().startswith(("betw", "btw")):
            name = f"between_{where_count}"
            kwarg_query += " BETWEEN %(" + name + "_low)s AND %(" + name + "_high)s"
            kwarg_params.update({f"{name}_low": value[1], f"{name}_high": value[2]})
        # WHERE column_name < val
        elif key.lower().startswith("lt"):
            name = f"lt_{where_count}"
            kwarg_query += " < %(" + name + ")s"
            kwarg_params.update({name: value[1]})
        # WHERE column_name > val
        elif key.lower().startswith("gt"):
            name = f"gt_{where_count}"
            kwarg_query += " > %(" + name + ")s"
            kwarg_params.update({name: value[1]})
        # WHERE column_name <= val
        elif key.lower().startswith("le"):
            name = f"le_{where_count}"
            kwarg_query += " <= %(" + name + ")s"
            kwarg_params.update({name: value[1]})
        # WHERE column_name >= val
        elif key.lower().startswith("ge"):
            name = f"ge_{where_count}"
            kwarg_query += " >= %(" + name + ")s"
            kwarg_params.update({name: value[1]})
        # WHERE column_name IN (val_a, val_b, val_c, val_d, ...)
        elif key.lower().startswith("in"):
            name = f"in_{where_count}"
            kwarg_query += " IN ("
            in_values = []
            for index, val in enumerate(value[1]):
                in_name = f"{name}_{index}"
                in_values += "%(" + in_name + ")s"
                kwarg_params.update({in_name: val})
            kwarg_query += ", ".join(in_values)
            kwarg_query += ")"

        # Hvis der ikke er tilføjet nogen parametre (dvs. hvis kwarg'et er ugyldigt),
        # så returneres en tom streng
        if not kwarg_params:
            kwarg_query = ''
        return kwarg_query, kwarg_params

    def _sort(self, column_name: ColumnName | tuple[ColumnName], order: int | str = 0, direction: str = 'a') -> str:
        """
        Konstruerer ORDER BY- og ASC/DESC-delen af et query.

        :param column_name: Navnet på kolonne(r)n(e), der er valgt og kan sorteres efter.
        :type column_name: str | tuple[str]
        :param order: Kolonnen, som resultatet ordnes efter.
            Enten *int*, der vælger indekset af kolonnen blandt de valgte kolonner,
            eller *str*, der vælger ud fra navnet på kolonnen.
            *Upåkrævet*. Standardværdi: ``0``
        :type order: int | str, optional
        :param direction:  Angiver hvilken retning, resultatet skal ordnes i.
            ``'a'``, ``"asc"`` eller ``"ascending"`` er opadgående rækkefølge, mens
            ``'d'``, ``"desc"`` eller ``"descending"`` er nedadgående rækkefølge.
            *Upåkrævet*. Standardværdi: ``'a'``
        :type direction: str, optional

        :return: ORDER BY-delen af et query.
        :rtype: str
        """
        query = ""
        # Formaterer nu kolonnenavne i tilfælde af database.tabel.kolonne-format
        if isinstance(order, int) and order >= 0 and order < len(column_name):
            query += f" ORDER BY {self._format_column(column_name[order])}"
        elif isinstance(order, str) and order in column_name:
            query += f" ORDER BY {self._format_column(order)}"
        if "ORDER BY" in query:
            if direction.lower() in ['a', "asc", "ascending"]:
                query += " ASC"
            elif direction.lower() in ['d', "desc", "descending"]:
                query += " DESC"

        return query

    def _limit(self, limit: int, offset: int = 0) -> tuple[str, Parameter]:
        """
        Konstruerer LIMIT- og OFFSET-delen af et query.

        :param limit: Begrænser antal læste rækker til et bestemt antal.
        :type limit: int
        :param offset: Bestemmer, hvor mange rækker, der springes over,
            inden læsning påbegyndes.
            *Upåkrævet*. Standardværdi: ``0``
        :type offset: int

        :return: En tuple bestående af en tekststreng til queriet,
            samt en dict med parametre til eksekveringen af queriet.
        :rtype: tuple[str, dict[str, Any]]
        """
        query = ''
        params = {}
        if isinstance(limit, int) and limit > 0:
            query += " LIMIT %(limit)s"
            params["limit"] = limit
        if isinstance(offset, int) and offset > 0:
            query += " OFFSET %(offset)s"
            params["offset"] = offset

        return query, params

    # TODO: Lav måske en slags auto-join ud fra foreign keys
    def _join(self,
        left: TableName,
        right: TableName,
        on_left: ColumnName,
        on_right: ColumnName,
        join_type: str = 'i',
    ) -> str:
        """
        Konstruerer JOIN-delen af et query.

        :param left: Den venstre tabel.
            *Påkrævet*.
        :type left: str
        :param right: Den højre tabel.
            *Påkrævet*.
        :type right: str
        :param on_left: Navnet på kolonnen, som der joines på i venstre tabel
            *Påkrævet*.
        :type on_left: str
        :param on_left: Navnet på kolonnen, som der joines på i højre tabel
            *Påkrævet*.
        :type on_left: str
        :param direction: Typen af join. Kan være
            ``'i'``, ``'o'``, ``'l'``, ``'r'``,
            ``"inner"``, ``"outer"``, ``"left"`` eller ``"right"``.
            *Påkrævet*. Standardværdi: ``'i'``
        :type direction: str

        :return: JOIN-delen af et query.
        :rtype: str
        :return: Hvis de to tabeller ikke kunne joines.
        :rtype: str: ``''``
        """
        tables = [table[0] for table in self.info()]
        for table in [left, right]:
            if table not in tables:
                print(f"Tabellen '{table}' findes ikke i databasen.")
                return ''
        left_columns = [column[0] for column in self.info(left)]        # hurtigere end list(zip(*self.info(left)))[0] ?
        right_columns = [column[0] for column in self.info(right)]      # hurtigere end list(zip(*self.info(left)))[0] ?
        if on_left not in left_columns or on_right not in right_columns:
            return ''

        join_query = ' '
        if join_type in ['i', "inner"]:
            join_query += "INNER "
        elif join_type in ['o', "outer"]:
            join_query += "OUTER "
        elif join_type in ['l', "left"]:
            join_query += "LEFT "
        elif join_type in ['r', "right"]:
            join_query += "RIGHT "

        join_query += f"JOIN `{right}` ON `{left}`.`{on_left}` = `{right}`.`{on_right}`"

        return join_query

    def info(self, table_name: TableName = '') -> DataField | list[tuple[TableName]] | bool:
        """
        Henter info om databasens eller en tabels opbygning.

        :param table_name: Navnet på tabellen, hvis info efterspørges.
            Hvis navnet er tomt, hentes info om databasen.
            *Påkrævet*. Standardværdi: ``''``
        :type table_name: str

        :return: En liste indeholdende en tuple med info for hver kolonne i tabellen.
            Tuplen indeholder navn, datatype, nullability, nøgletype, standardværdi og .
        :rtype: list[tuple[str, str, str, str, typing.Any, str]]
        :return: En liste indeholdende info om hver tabel i databasen, herunder navn.
        :rtype: list[tuple[str]]
        :return: Hvis READ-operationen ikke kunne gennemføres.
            Enten fordi der ikke er nogen forbindelse til en database,
            eller forbi tabellen eller databasen ikke eksisterer.
        :rtype: bool: ``False``
        """
        if table_name:
            describe_query = f"DESCRIBE `{table_name}`"
        else:
            describe_query = "SHOW TABLES"

        self._preview(describe_query)

        # Hvis handlingen gennemføres, printes succesbesked
        if table_info := self._execute(describe_query, read=True):
            if table_name:
                print(f"SUCCES: Hentede info om tabellen '{table_name}'.")
            else:
                print(f"SUCCES: Hentede info om databasen '{self.database}'.")
        return table_info

    def get_header(self, table: TableName | DataField) -> TableHeader:
        header = {}
        if isinstance(table, str):
            table = self.info(table)
        for column_info in table:
            header[column_info[0]] = {
                "type": column_info[1],
                "nullable": True if column_info[2] == "YES" else False,
                #"key": ,
                "default": column_info[4],
                "extra": column_info[5]
            }
        return header

    def _find_constraints(self, table: TableName | DataField, primary: bool = True) -> ColumnName | ConstraintList:
        if isinstance(table, str):
            table = self.info(table)
        keys = [column_info[0] for column_info in table if column_info[3] == ("PRI" if primary else "UNI")]
        return keys[0] if len(keys) == 1 else keys

    def primary_keys(self, table: TableName | DataField) -> ColumnName | ConstraintList:
        return self._find_constraints(table, True)

    def unique_keys(self, table: TableName | DataField) -> ColumnName | ConstraintList:
        return self._find_constraints(table, False)

    def foreign_keys(self, table_name: TableName) -> ForeignKeys:
        # primary_keys = []
        foreign_keys = {}

        # Læser info om databasen
        constraints = self.read(
            "INFORMATION_SCHEMA.KEY_COLUMN_USAGE",
            "CONSTRAINT_SCHEMA", "CONSTRAINT_NAME",
            #"TABLE_SCHEMA",
            "TABLE_NAME", "COLUMN_NAME",
            #"REFERENCED_TABLE_SCHEMA",
            "REFERENCED_TABLE_NAME", "REFERENCED_COLUMN_NAME",
            eq=("CONSTRAINT_SCHEMA", self.database),
            eq2=("TABLE_NAME", table_name)
        )
        for constraint in constraints:
            # Finder primary key(s)
            # if constraint["CONSTRAINT_NAME"] == "PRIMARY":
            #     primary_keys.append(constraint["COLUMN_NAME"])
            # Finder foreign keys
            if constraint["REFERENCED_TABLE_NAME"] is not None:
                foreign_keys[constraint["COLUMN_NAME"]] = (
                    constraint["REFERENCED_TABLE_NAME"],
                    constraint["REFERENCED_COLUMN_NAME"],
                )

        return foreign_keys

    def get_keys(self, table_name: TableName, table_info: DataField = []) -> Keys:
        keys = Keys()
        if not table_info:
            table_info = self.info(table_name)

        # Finder de forskellige typer keys
        foreign_keys = self.foreign_keys(table_name)
        primary_keys = self.primary_keys(table_info)
        unique_keys = self.unique_keys(table_info)
        # Hvis der er én primary key, sættes den på for sig selv
        # Hvis der er en multicol pk, sættes hele listen på
        if primary_keys:
            keys.primary = primary_keys
        # Hvis der er foreign keys, sættes hele dicten på
        if foreign_keys:
            keys.foreign = foreign_keys
        # Hvis der er unikke keys, sættes de på (samme procedure som for pk)
        if unique_keys:
            keys.unique = unique_keys

        return keys

    def get_table(self, table_name: TableName) -> Table:
        # Finder grundlæggende info
        table_info = self.info(table_name)

        # Indsætter tabelnavn
        table = {"name": table_name}
        # Indsætter header
        table["header"] = self.get_header(table_info)
        # Indsætter primary, foreign og unique keys
        table["keys"] = self.get_keys(table_name, table_info)
        # Indsætter data
        table["data"] = self.read(table_name)

        return table

    # UPDATE-operationer
    def update(self,
        table_name: TableName,
        change: ColumnName,
        new_value: typing.Any,
        **kwargs
    ) -> None:
        """
        _summary_

        :param table_name: Tabellen, hvori data skal opdateres.
        :type table_name: str
        :param change: Kolonnen, hvor værdien ændres.
        :type change: str
        :param new_value: Værdien, der ændres til.
        :type new_value: Any
        """
        # UPDATE TABLE table_name
        # SET change = new_value
        # WHERE where = old_value
        # WHERE bruger self._where()
        pass

    def add(self, table_name: TableName, column_name: ColumnName, datatype: str) -> None:
        # ALTER TABLE table_name ADD colum_name datatype
        pass

    def modify(self, table_name: TableName, column_name: ColumnName, datatype: str) -> None:
        # ALTER TABLE table_name MODIFY COLUMN column_name datatype
        pass

    def primary_key(self, table_name: TableName, column_name: ColumnName) -> None:
        alter_query = f"ALTER TABLE `{table_name}` ADD PRIMARY KEY (`{column_name}`)"

        self._preview(alter_query)
        if self._execute(alter_query):
            print(f"SUCCES: Tilføjede kolonnen '{column_name}' som primary key for tabellen '{table_name}'")

    def foreign_key(self, table_name: TableName, foreign_key: dict[str, str]) -> None: # dict[ColumnName, tuple[TableName, ColumnName]]
        alter_queries = []
        for key in foreign_key:
            split_key = foreign_key[key].split('.')
            alter_query = f"ALTER TABLE `{table_name}` "
            alter_query += f"ADD FOREIGN KEY (`{key}`) REFERENCES `{split_key[0]}`(`{split_key[1]}`)"
            alter_queries.append(alter_query)

        for query in alter_queries:
            self._preview(query)
            if self._execute(query):
                print(f"SUCCES: Tilføjede foreign key til tabellen '{table_name}'.")


    # DELETE-operationer
    def delete(self, table_name: TableName, where: ColumnName, value: str) -> None:
        # DELETE FROM table_name WHERE where = value
        # if not where and not value:
        #   DELETE FROM table_name
        # (langsommere end TRUNCATE / self.empty(),
        # fordi det gemmer til transaktionsloggen og kan rulles tilbage)
        pass

    # TODO: DROP kan også bruges på en hel database eller en kolonne:
    # DROP DATABASE database
    # ALTER TABLE table_name DROP COLUMN column_name
    def drop(self, table_name: TableName, force: bool = False) -> None:
        """
        Fjerner en tabel helt fra databasen.

        :param table_name: Navnet på tabellen, der ønskes fjernet.
            *Påkrævet*.
        :type table_name: str
        :param force: Bestemmer om bekræftelse af operation skal springes over.
            *Upåkrævet*. Standardværdi: ``False``
        :type force: bool
        """
        drop_query = f"DROP TABLE `{table_name}`"

        self._preview(drop_query)

        # Det er altid godt at bekræfte ved DELETE-operationer
        confirmation = f"Er du sikker på, at du gerne vil nulstille databasen '{self.database}'? (j/N) "
        if force or input(confirmation).lower() in ['j', 'y']:
            # Hvis query gennemføres, printes positivt resultat
            if self._execute(drop_query):
                print(f"SUCCES: Tabellen '{table_name}' blev fjernet.")

    def empty(self, table_name: TableName, force: bool = False) -> None:
        """
        Rydder en tabel for al data, men fjerner ikke tabellen.

        :param table_name: Navnet på tabellen, der ønskes ryddet for data.
            *Påkrævet*.
        :type table_name: str
        :param force: Bestemmer om bekræftelse af operation skal springes over.
            *Upåkrævet*. Standardværdi: ``False``
        :type force: bool
        """
        truncate_query = f"TRUNCATE TABLE `{table_name}`"

        self._preview(truncate_query)

        # Det er altid godt at bekræfte ved DELETE-operationer
        confirmation = f"Er du sikker på, at du gerne vil nulstille databasen '{self.database}'? (j/N) "
        if force or input(confirmation).lower() in ['j', 'y']:
            # Hvis query gennemføres, printes positivt resultat
            if self._execute(truncate_query):
                print(f"SUCCES: Tabellen '{table_name}' blev ryddet for data.")

    def reset(self, force: bool = False) -> None:
        """
        Nulstiller databasen.

        Sletter nuværende database og gendanner derefter en tom database med samme navn.

        :param force: Bestemmer om bekræftelse af operation skal springes over.
            *Upåkrævet*. Standardværdi: False
        :type force: bool
        """
        drop_query = f"DROP DATABASE `{self.database}`"

        self._preview(drop_query)

        # Det er altid godt at bekræfte ved DELETE-operationer
        confirmation = f"Er du sikker på, at du gerne vil nulstille databasen '{self.database}'? (j/N) "
        if force or input(confirmation).lower() in ['j', 'y']:
            # Hvis begge queries gennemføres, printes positivt resultat
            if self._execute(drop_query) and self.create_database(self.database):
                print(f"Databasen '{self.database}' blev nulstillet.")
                # Skal logge ind igen for at forny forbindelserne
                self.login()

def main() -> None:
    pass

if __name__ == "__main__":
    main()
