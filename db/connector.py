import mysql.connector
import getpass

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
    :param host: Adressen på serveren, der forbindes til.
        Hvis tom, bruges MySQL-standarden ``"127.0.0.1"``.
        *Upåkrævet*. Standardværdi: ``''``
    :type host: str
    :param port: Porten, der forbindes til.
        Hvis tom, bruges MySQL-standarden ``"3306"``.
        *Upåkrævet*. Standardværdi: ``''``
    :type port: str
    """

    def __init__(self,
        username: str = '',
        password: str = '',
        database: str = '',
        host: str = '',
        port: str = ''
    ) -> None:
        """
        Konstruktøren af connector-objektet.

        Hvis info ikke gives som input i oprettelsen af objektet, kan brugeren selv indtaste det i terminalen.

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
        :param host: Adressen på serveren, der forbindes til.
            Hvis tom, bruges MySQL-standarden ``"127.0.0.1"``.
            *Upåkrævet*. Standardværdi: ``''``
        :type host: str
        :param port: Porten, der forbindes til.
            Hvis tom, bruges MySQL-standarden ``"3306"``.
            *Upåkrævet*. Standardværdi: ``''``
        :type port: str
        """
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

        # Anden adresse end standarden '127.0.0.1:3306' kan defineres
        self.host = host
        self.port = port

        # Forsøger at oprette forbindelser
        self._first_login(password)

    def _error(msg: str, *err: str) -> None:
        # Ad, grim quickfix af fejl
        if len(err) > 1:
            msg = err[-2]
            err = err[-1]

        error_message = f"FEJL: {msg}"
        if err:
            error_message += f" Følgende fejl opstod:\n    {err}"
        print(error_message)

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
        }
        # Tilføj kun specifik database, hvis den er defineret
        if db:
            login_params["database"] = self.database
        # Hvis disse er tomme, bruger MySQL som standard '127.0.0.1:3306'
        if self.host:
            login_params["host"] = self.host
        if self.port:
            login_params["port"] = self.port

        try:
            # Dict udpakkes og bruges som keyword-parametre i oprettelse af forbindelsen
            connection = mysql.connector.connect(**login_params)
        except Exception as err:
            self._error("Kunne ikke oprette forbindelsen.", err)
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
            self._error("Kunne ikke genoprette forbindelsen.", err)
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
