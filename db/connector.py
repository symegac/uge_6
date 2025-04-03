import mysql.connector
import getpass

# TODO: Kan i fremtiden udvides til også at benyttes til andre servere end localhost
# TODO: Tilføj måde at prøve login igen, hvis forbindelse ikke kunne oprettes pga. forkert logininfo
class DatabaseConnector:
    """
    Henter og gemmer loginoplysninger til en serverforbindelse, evt. en specifik database,
    og bruger disse til at oprette forbindelsen.

    :param username: Brugernavnet, der skal bruges til at logge ind med.
        *Påkrævet*. Standardværdi: ``''``
    :type username: str
    :param password: Adgangskoden, der skal bruges til at logge ind med.
        *Påkrævet*. Standardværdi: ``''``
    :type password: str
    :param database: Navnet på databasen, der evt. skal forbindes til.
        Er dette navn tomt, oprettes forbindelsen uden noget specifikt mål.
        *Upåkrævet*. Standardværdi: ``''``
    :type database: str
    """

    def __init__(self,
        username: str = '',
        password: str = '',
        database: str = '',
        host: str = "localhost",
        port: str = "3306"
    ) -> None:
        """
        Konstruktøren af connector-objektet.

        Hvis info ikke gives som input i oprettelsen af objektet, kan brugeren selv indtaste det i terminalen.
        """
        self.host = host
        self.port = port

        if not username:
            self.username = input("Indtast brugernavn: ")
        else:
            self.username = username

        # Gemmer ikke password som attribut, så man ikke kan sige
        # >>> database.password
        # og få fat i koden i klartekst
        # Når forbindelsen gemmes, kan man alligevel bare bruge den
        # uden at skulle permanent gemme adgangskoden
        if not password:
            password = getpass.getpass("Indtast adgangskode: ")

        # Databasenavne er som standard case insensitive i MySQL
        # Man kunne måske lave mere validering af det angivne databasenavns format
        if not database:
            self.database = input("Indtast databasenavn (eller blank for direkte login): ")
        else:
            self.database = database

        # Forsøger at oprette forbindelser
        self._first_login(password)

    def _login(self, password: str, db: bool = True) -> mysql.connector.MySQLConnection | bool:
        """
        Opretter forbindelse til en database.

        Bruger oplysningerne angivet ved connectorens oprettelse til at logge ind
        og oprette en forbindelse til en database, eller evt. direkte uden specifikt mål.

        :param password: Adgangskoden til forbindelsen, der ønskes oprettet.
            *Påkrævet*.
        :type password: str
        :param db: Angiver om der skal forbindes til en specifik database.
            *Upåkrævet*. Standardværdi: ``True``
        :type db: bool

        :return: Forbindelsen til en database, eller en direkte forbindelse.
        :rtype: mysql.connector.MySQLConnection
        :return: En forbindelse kunne ikke oprettes.
        :rtype: bool: ``False``
        """
        login_params = {
            "user": self.username,
            "password": password,
            "host": self.host
        }
        # Tilføj kun specifik database, hvis den er defineret
        if db:
            login_params["database"] = self.database

        try:
            # Dict udpakkes og bruges som keyword-parametre i oprettelse af forbindelsen
            connection = mysql.connector.connect(**login_params)
        except Exception as err:
            print("FEJL: Kunne ikke oprette forbindelsen. Følgende fejl opstod:\n    ", err)
            return False

        return connection

    def _first_login(self, password: str):
        """
        :param password: Adgangskoden, der bruges til at forbinde til server og database.
            *Påkrævet*.
        :type password: str
        """
        # Forbinder direkte... (skal bruges til oprettelse eller nulstilling)
        self.direct_connection = self._login(password, db=False)
        if self.direct_connection:
            print("SUCCES: Forbundet til serveren.")
        # ...og til specifik database, hvis self.database er truthy (dvs. ikke tom)
        if self.database:
            self.connection = self._login(password, db=True)
            if self.connection:
                print(f"SUCCES: Forbundet til databasen '{self.database}'.")

    def login(self) -> None:
        """
        Genåbner forbindelserne til server og database,
        hvis de er blevet lukket efter konstruktionen af databasen.
        """
        # Forbindelserne beholder deres indstillinger, så man kan let genåbne dem igen.
        try:
            self.direct_connection.connect()
            self.connection.connect()
        except Exception as err:
            print("FEJL: Kunne ikke genoprette forbindelsen. Følgende fejl opstod:\n    ", err)
        else:
            print(f"SUCCES: Genoprettede forbindelsen til serveren og databasen '{self.database}'.")

    def logout(self) -> None:
        """
        Lukker forbindelserne til database og server.
        """
        self.connection.close()
        print(f"SUCCES: Lukkede forbindelsen til databasen '{self.database}'.")
        self.direct_connection.close()
        print("SUCCES: Lukkede forbindelsen til serveren.")

if __name__ == "__main__":
    connection = DatabaseConnector()
    print(connection.connection)

# Den gamle navnevalidering
# RESERVED = ["ACCESSIBLE", "ADD", "ALL", "ALTER", "ANALYZE", "AND", "AS", "ASC", "ASENSITIVE", "BEFORE", "BETWEEN", "BIGINT", "BINARY", "BLOB", "BOTH", "BY", "CALL", "CASCADE", "CASE", "CHANGE", "CHAR", "CHARACTER", "CHECK", "COLLATE", "COLUMN", "CONDITION", "CONSTRAINT", "CONTINUE", "CONVERT", "CREATE", "CROSS", "CUBE", "CUME_DIST", "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP", "CURRENT_USER", "CURSOR", "DATABASE", "DATABASES", "DAY_HOUR", "DAY_MICROSECOND", "DAY_MINUTE", "DAY_SECOND", "DEC", "DECIMAL", "DECLARE", "DEFAULT", "DELAYED", "DELETE", "DENSE_RANK", "DESC", "DESCRIBE", "DETERMINISTIC", "DISTINCT", "DISTINCTROW", "DIV", "DOUBLE", "DROP", "DUAL", "EACH", "ELSE", "ELSEIF", "EMPTY", "ENCLOSED", "ESCAPED", "EXCEPT", "EXISTS", "EXIT", "EXPLAIN", "FALSE", "FETCH", "FIRST_VALUE", "FLOAT", "FLOAT4", "FLOAT8", "FOR", "FORCE", "FOREIGN", "FROM", "FULLTEXT", "FUNCTION", "GENERATED", "GET", "GRANT", "GROUP", "GROUPING", "GROUPS", "HAVING", "HIGH_PRIORITY", "HOUR_MICROSECOND", "HOUR_MINUTE", "HOUR_SECOND", "IF", "IGNORE", "IN", "INDEX", "INFILE", "INNER", "INOUT", "INSENSITIVE", "INSERT", "INT", "INT1", "INT2", "INT3", "INT4", "INT8", "INTEGER", "INTERSECT", "INTERVAL", "INTO", "IO_AFTER_GTIDS", "IO_BEFORE_GTIDS", "IS", "ITERATE", "JOIN", "JSON_TABLE", "KEY", "KEYS", "KILL", "LAG", "LAST_VALUE", "LATERAL", "LEAD", "LEADING", "LEAVE", "LEFT", "LIKE", "LIMIT", "LINEAR", "LINES", "LOAD", "LOCALTIME", "LOCALTIMESTAMP", "LOCK", "LONG", "LONGBLOB", "LONGTEXT", "LOOP", "LOW_PRIORITY", "MASTER_BIND", "MASTER_SSL_VERIFY_SERVER_CERT", "MATCH", "MAXVALUE", "MEDIUMBLOB", "MEDIUMINT", "MEDIUMTEXT", "MIDDLEINT", "MINUTE_MICROSECOND", "MINUTE_SECOND", "MOD", "MODIFIES", "NATURAL", "NOT", "NO_WRITE_TO_BINLOG", "NTH_VALUE", "NTILE", "NULL", "NUMERIC", "OF", "ON", "OPTIMIZE", "OPTIMIZER_COSTS", "OPTION", "OPTIONALLY", "OR", "ORDER", "OUT", "OUTER", "OUTFILE", "OVER", "PARTITION", "PERCENT_RANK", "PRECISION", "PRIMARY", "PROCEDURE", "PURGE", "RANGE", "RANK", "READ", "READS", "READ_WRITE", "REAL", "RECURSIVE", "REFERENCES", "REGEXP", "RELEASE", "RENAME", "REPEAT", "REPLACE", "REQUIRE", "RESIGNAL", "RESTRICT", "RETURN", "REVOKE", "RIGHT", "RLIKE", "ROW", "ROWS", "ROW_NUMBER", "SCHEMA", "SCHEMAS", "SECOND_MICROSECOND", "SELECT", "SENSITIVE", "SEPARATOR", "SET", "SHOW", "SIGNAL", "SMALLINT", "SPATIAL", "SPECIFIC", "SQL", "SQLEXCEPTION", "SQLSTATE", "SQLWARNING", "SQL_BIG_RESULT", "SQL_CALC_FOUND_ROWS", "SQL_SMALL_RESULT", "SSL", "STARTING", "STORED", "STRAIGHT_JOIN", "SYSTEM", "TABLE", "TERMINATED", "THEN", "TINYBLOB", "TINYINT", "TINYTEXT", "TO", "TRAILING", "TRIGGER", "TRUE", "UNDO", "UNION", "UNIQUE", "UNLOCK", "UNSIGNED", "UPDATE", "USAGE", "USE", "USING", "UTC_DATE", "UTC_TIME", "UTC_TIMESTAMP", "VALUES", "VARBINARY", "VARCHAR", "VARCHARACTER", "VARYING", "VIRTUAL", "WHEN", "WHERE", "WHILE", "WINDOW", "WITH", "WRITE", "XOR", "YEAR_MONTH", "ZEROFILL"]
# if ';' in name:
    #     print("Illegal name! Can't contain ';'!")
    #     quit()
    # for word in self.RESERVED:
    #     if f"{word} " in name.upper():
    #         print(f"Illegal name! Can't contain MySQL reserved word {word}!")
    #         quit()
