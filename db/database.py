import getpass
import typing
from . import util
from . import connector
from intertable import *

class Database(connector.DatabaseConnector):
    """
    Et objekt, der er forbundet til en MySQL-instans og som regel en database heri,
    og som kan interagere med databasen og tabellerne, som den indeholder.

    :param username: Brugernavnet, der skal bruges til at logge ind med.
        *Påkrævet*. Standardværdi: `''`
    :type username: str
    :param password: Adgangskoden, der skal bruges til at logge ind med.
        *Påkrævet*. Standardværdi: `''`
    :type password: str
    :param database: Navnet på databasen, der evt. skal forbindes til.
        *Upåkrævet*. Standardværdi: `''`
    :type database: str
    :param host: Adressen på serveren, der forbindes til.
        Hvis tom, bruges MySQL-standarden `"127.0.0.1"`.
        *Upåkrævet*. Standardværdi: `''`
    :type host: str
    :param port: Porten, der forbindes til.
        Hvis tom, bruges MySQL-standarden `"3306"`.
        *Upåkrævet*. Standardværdi: `''`
    :type port: str
    :param init_load: En liste over tabeller, der ved initialisering automatisk skal
        indlæses i databasen.
        *Upåkrævet*. Standardværdi: `[]`
    :type init_load: list[InterTable]
    :param preview: Bestemmer, om queries skal forhåndsvises inden eksekvering.
        *Upåkrævet*. Standardværdi: `True`
    :type preview: bool
    """
    def __init__(self,
        username: str = '',
        password: str = '',
        database: str = '',
        host: str = '',
        port: str = '',
        init_load: list[InterTable] = [],
        preview: bool = True,
    ) -> None:
        """
        Konstruktøren af database-objektet.

        :param username: Brugernavnet, der skal bruges til at logge ind med.
            *Påkrævet*. Standardværdi: `''`
        :type username: str
        :param password: Adgangskoden, der skal bruges til at logge ind med.
            *Påkrævet*. Standardværdi: `''`
        :type password: str
        :param database: Navnet på databasen, der evt. skal forbindes til.
            *Upåkrævet*. Standardværdi: `''`
        :type database: str
        :param host: Adressen på serveren, der forbindes til.
            Hvis tom, bruges MySQL-standarden `"127.0.0.1"`.
            *Upåkrævet*. Standardværdi: `''`
        :type host: str
        :param port: Porten, der forbindes til.
            Hvis tom, bruges MySQL-standarden `"3306"`.
            *Upåkrævet*. Standardværdi: `''`
        :type port: str
        :param init_load: En liste over datafiler, der ved initialisering automatisk skal
            indlæses som tabeller i databasen.
            *Upåkrævet*. Standardværdi: `[]`
        :type init_load: list[str]
        :param preview: Bestemmer, om queries skal forhåndsvises inden eksekvering.
            *Upåkrævet*. Standardværdi: `True`
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
            *Upåkrævet*. Standardværdi: `{}`
        :type params: dict[str, Any] | list[dict[str, Any]]
        :param db: Bestemmer om handlingen udføres i en specifik database eller direkte.
            Skal være `False` ved f.eks. oprettelse af ny database eller nulstilning af database.
            *Påkrævet*. Standardværdi: `True`
        :type db: bool
        :param read: Bestemmer, om der skal bruges en buffered cursor,
            så data kan læses og fetches fra databasen.
            *Upåkrævet*. Standardværdi: `False`
        :type read: bool

        :return: Queriet kunne eksekveres, og handlingen blev gennemført.
        :rtype: bool: `True`
        :return: Handlingen kunne ikke gennemføres.
        :rtype: bool: `False`
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

    def create(self, table: InterTable) -> None:
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
        table_name = table.name
        columns = table.header
        keys = table.keys

        create_query = f"CREATE TABLE `{table_name}` ("

        column_queries = []
        column_params = {}

        for column in columns:
            field = columns[column]
            column_query = f"`{field.name}` {field.datatype}"
            if not field.nullable:
                column_query += " NOT NULL"
            # TODO: Fiks default-værdier (1067 (42000): Invalid default value for 'col')
            if field.default is not None:
                column_query += " DEFAULT %(" + field.name + "_default)s"
                column_params.update({f"{field.name}_default": field.default})
            if field.extra:
                column_query += ' ' + field.extra
            column_queries.append(column_query)
        create_query += ", ".join(column_queries)

        if keys is not None:
            create_query += f", {self._create_keys(keys, table_name)}"

        create_query += ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci'

        self._preview(create_query)

        if self._execute(create_query, column_params):
            print(f"SUCCES: Oprettede tabellen '{table_name}'.")

    def _create_keys(self, keys: Keys, table_name: TableName) -> str:
        keylist = []
        if primary := keys.primary:
            if isinstance(primary, list):
                # TODO: Kan kun have to kolonner som multikey lige nu
                primary_key = f"CONSTRAINT PK_{primary[0]}_{primary[1]} PRIMARY KEY (`{primary[0]}`,`{primary[1]}`)"
            else:
                primary_key = f"PRIMARY KEY (`{primary}`)"
            keylist.append(primary_key)
        if foreign := keys.foreign:
            fklist = [f"CONSTRAINT FK_{table_name}_{key}_{foreign[key][0]}_{foreign[key][1]} FOREIGN KEY (`{key}`) REFERENCES `{foreign[key][0]}`(`{foreign[key][1]}`)" for key in foreign]
            keylist.extend(fklist)
        if unique := keys.unique:
            if isinstance(unique, list):
                # TODO: Kan kun have to kolonner som multikey lige nu
                unique_key = f"CONSTRAINT UC_{unique[0]}_{unique[1]} UNIQUE (`{unique[0]}`,`{unique[1]}`)"
            else:
                unique_key = f"UNIQUE (`{unique}`)"
            keylist.append(unique_key)
        return ", ".join(keylist)

    # TODO: Implementér et system til at skippe eller overwrite, hvis et felt i en række i datasættet
    # har samme værdi som ditto i tabellen. Hvis altså kolonnen har PRIMARY KEY eller UNIQUE som constraint.

    # None eller ikke-eksisterende keys -> default value hvis DEFAULT -> NULL hvis nullable -> fejl
    def insert(self, data: InterTable) -> None:
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
            Hvis `True` forsøges dataen desuden at matches med den angivne tabels kolonnenavne.
            *Upåkrævet*. Standardværdi: `True`
        :type header: bool

        :return: Hvis tabellen ikke findes, eller hvis dataene ikke har samme antal kolonner som tabellen.
        :rtype: None
        """
        table_name = data.name
        header = data.header

        # Danner query
        insert_query = f"INSERT INTO `{table_name}` ("
        # Kolonnenavne (med backticks, fordi navnene er taget fra tabellen)
        insert_query += ", ".join([f"`{header[column].name}`" for column in header]) + ") VALUES ("
        # Kolonneværdier (med %()s, fordi det er værdier oplyst af brugeren, der skal tjekkes)
        insert_query += ", ".join([f"%({header[column].name})s" for column in header]) + ')'

        # Danner dict over parametre til indsættelse af data
        insert_params = data.data

        self._preview(insert_query)

        if self._execute(insert_query, insert_params):
            print(f"SUCCES: DataList indsat i tabellen '{table_name}'.")

    def load(self, *tables: InterTable) -> None:
        """
        Indlæser en eller flere tabeller i databasen.

        :param tables: En eller tabeller, der skal indlæses i databasen.
        :type tables: InterTable
        """
        for table in tables:
            self.create(table)
            self.insert(table)

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
    ) -> DataList | None:
        """
        Læser data fra en tabel.

        :param table_name: Navnet på den tabel, som data skal læses fra.
            *Påkrævet*.
        :type table_name: str
        :param column_name: Navnet eller navnene på den kolonne eller de kolonner, som data skal læses fra.
            *Upåkrævet*.
        :type column_name: str
        :param joins: En liste med en dict indeholdende parametrene for hvert join, der skal indsættes i queriet.
            Et join har som regel formen `{
                "right": tabel_2,
                "on_left": kolonne_1,
                "on_right": kolonne_2.
                "join_type": JOIN-type
            }` i brug, men parameteren `"left"` kan også oplyses om nødvendigt.
            *Upåkrævet*. Standardværdi: `[]`
        :type joins: list[dict[str, str]]
        :param order: Kolonnen, som resultatet ordnes efter.
            Enten *int*, der vælger indekset af kolonnen blandt de valgte kolonner,
            eller *str*, der vælger ud fra navnet på kolonnen.
            *Upåkrævet*. Standardværdi: `0`
        :type order: int | str
        :param direction: Angiver hvilken retning, resultatet skal ordnes i.
            `'a'`, `"asc"` eller `"ascending"` er opadgående rækkefølge, mens
            `'d'`, `"desc"` eller `"descending"` er nedadgående rækkefølge.
            *Upåkrævet*. Standardværdi: `'a'`
        :type direction: str
        :param limit: Mængden af rækker, der skal læses.
            Når værdien er `0`, læses alle resultater.
            *Upåkrævet*. Standardværdi: `0`
        :type limit: int
        :param offset: Mængden af rækker, der springes over, inden læsningen påbegyndes.
            Når værdien er `0`, læses alle resultater.
            *Upåkrævet*. Standardværdi: `0`
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
        # TODO: DRY
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
            *Upåkrævet*. Standardværdi: `0`
        :type order: int | str, optional
        :param direction:  Angiver hvilken retning, resultatet skal ordnes i.
            `'a'`, `"asc"` eller `"ascending"` er opadgående rækkefølge, mens
            `'d'`, `"desc"` eller `"descending"` er nedadgående rækkefølge.
            *Upåkrævet*. Standardværdi: `'a'`
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
            *Upåkrævet*. Standardværdi: `0`
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
            `'i'`, `'o'`, `'l'`, `'r'`,
            `"inner"`, `"outer"`, `"left"` eller `"right"`.
            *Påkrævet*. Standardværdi: `'i'`
        :type direction: str

        :return: JOIN-delen af et query.
        :rtype: str
        :return: Hvis de to tabeller ikke kunne joines.
        :rtype: str: `''`
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
            *Påkrævet*. Standardværdi: `''`
        :type table_name: str

        :return: En liste indeholdende en tuple med info for hver kolonne i tabellen.
            Tuplen indeholder navn, datatype, nullability, nøgletype, standardværdi og .
        :rtype: list[tuple[str, str, str, str, typing.Any, str]]
        :return: En liste indeholdende info om hver tabel i databasen, herunder navn.
        :rtype: list[tuple[str]]
        :return: Hvis READ-operationen ikke kunne gennemføres.
            Enten fordi der ikke er nogen forbindelse til en database,
            eller forbi tabellen eller databasen ikke eksisterer.
        :rtype: bool: `False`
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

    def get_header(self, table: TableName | DataField) -> Header:
        header = {}
        if isinstance(table, str):
            table = self.info(table)
        for column_info in table:
            info = {
                "name": column_info[0],
                "datatype": column_info[1],
                "nullable": True if column_info[2] == "YES" else False,
                #"key"
                "default": column_info[4],
                "extra": column_info[5]
            }
            header[info["name"]] = DataField(**info)
        return header

    def _find_constraints(self, table: TableName | DataField, primary: bool = True) -> ColumnName | list[ColumnName]:
        if isinstance(table, str):
            table = self.info(table)
        keys = [column_info[0] for column_info in table if column_info[3] == ("PRI" if primary else "UNI")]
        return keys[0] if len(keys) == 1 else keys

    def get_primary_keys(self, table: TableName | DataField) -> ColumnName | list[ColumnName]:
        return self._find_constraints(table, True)

    def get_unique_keys(self, table: TableName | DataField) -> ColumnName | list[ColumnName]:
        return self._find_constraints(table, False)

    def get_foreign_keys(self, table_name: TableName) -> ForeignKeys:
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
        foreign_keys = self.get_foreign_keys(table_name)
        primary_keys = self.get_primary_keys(table_info)
        unique_keys = self.get_unique_keys(table_info)
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

    def get_table(self, table_name: TableName, new_name: TableName = '', *args, **kwargs) -> InterTable:
        # Finder grundlæggende info
        table_info = self.info(table_name)

        # Finder header
        header = self.get_header(table_info)
        # Finder primary, foreign og unique keys
        keys = self.get_keys(table_name, table_info)
        # Finder data
        data = self.read(table_name, *args, **kwargs)

        # Opretter InterTable
        table = InterTable(new_name if new_name else table_name, header, keys, data)

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

    def add_column(self, table_name: TableName, column_name: ColumnName, datatype: str) -> None:
        # ALTER TABLE table_name ADD column_name datatype
        pass

    def modify_column(self, table_name: TableName, column_name: ColumnName, datatype: str) -> None:
        # ALTER TABLE table_name MODIFY COLUMN column_name datatype
        pass

    def add_primary_key(self, table_name: TableName, column_name: ColumnName) -> None:
        alter_query = f"ALTER TABLE `{table_name}` ADD PRIMARY KEY (`{column_name}`)"

        self._preview(alter_query)
        if self._execute(alter_query):
            print(f"SUCCES: Tilføjede kolonnen '{column_name}' som primary key for tabellen '{table_name}'")

    def add_foreign_keys(self, table_name: TableName, foreign_key: dict[str, tuple[str, str]]) -> None:
        alter_queries = []
        for key in foreign_key:
            reference = foreign_key[key]
            alter_query = f"ALTER TABLE `{table_name}` "
            alter_query += f"ADD FOREIGN KEY (`{key}`) REFERENCES `{reference[0]}`(`{reference[1]}`)"
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
            *Upåkrævet*. Standardværdi: `False`
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
            *Upåkrævet*. Standardværdi: `False`
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
