import datetime
from db.database import Database
from config import *

def main() -> None:
    db = Database(DB.localusername, DB.localpassword, "northwind")
    very_specific_query = db.read(
        "employees",
        "EmployeeID", "TitleOfCourtesy", "FirstName", "LastName", "Title", "BirthDate", "Country",
        like=("TitleOfCourtesy","Mr%"),
        like_2=("LastName","%a%"),
        lt=("BirthDate", datetime.date(1960, 1, 1)),
        between=("EmployeeID", 3, 8),
        order="LastName"
    )
    # >>> SELECT `EmployeeID`, `TitleOfCourtesy`, `FirstName`, `LastName`, `Title`, `BirthDate`, `Country` FROM `employees` WHERE `TitleOfCourtesy` LIKE %(like_0)s AND `LastName` LIKE %(like_1)s AND `BirthDate` < %(lt_2)s AND `EmployeeID` BETWEEN %(between_3_low)s AND %(between_3_high)s ORDER BY `LastName` ASC
    # før [(5, 'Mr.', 'Steven', 'Buchanan', 'Sales Manager', datetime.datetime(1955, 3, 4, 0, 0), 'UK'), (4, 'Mrs.', 'Margaret', 'Peacock', 'Sales Representative', datetime.datetime(1937, 9, 19, 0, 0), 'USA')]
    # nu= [{'EmployeeID': 5, 'TitleOfCourtesy': 'Mr.', 'FirstName': 'Steven', 'LastName': 'Buchanan', 'Title': 'Sales Manager', 'BirthDate': datetime.datetime(1955, 3, 4, 0, 0), 'Country': 'UK'}, {'EmployeeID': 4, 'TitleOfCourtesy': 'Mrs.', 'FirstName': 'Margaret', 'LastName': 'Peacock', 'Title': 'Sales Representative', 'BirthDate': datetime.datetime(1937, 9, 19, 0, 0), 'Country': 'USA'}]
    print(very_specific_query)

if __name__ == "__main__":
    main()