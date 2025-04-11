import re
import typing
from decimal import Decimal
from datetime import date, datetime, time
from collections import deque
from copy import deepcopy

Parameter = typing.NewType("Parameter", dict[str, typing.Any])
"""
:param Parameter:
:type Parameter: dict[str, typing.Any]
"""
ColumnName = typing.NewType("ColumnName", str)
"""
:param ColumnName:
:type ColumnName: str
"""
DataEntry = typing.NewType("DataEntry", dict[ColumnName, typing.Any])
"""
:param DataEntry:
:type DataEntry: dict[str, typing.Any]
"""
TableName = typing.NewType("TableName", str)
"""
:param TableName:
:type TableName: str
"""
ForeignKeys = typing.NewType("ForeignKeys", dict[ColumnName, tuple[TableName, ColumnName]])
"""
:param ForeignKeys:
:type ForeignKeys: dict[ColumnName, tuple[TableName, ColumnName]]
"""
DataList = typing.NewType("DataList", deque[DataEntry])
"""
:param DataList:
:type DataList: deque[DataEntry]
"""

# MYSQL_TYPES = {
#     str: ["varchar(", "char(", "tinytext", "text", "mediumtext", "longtext"],
#     int: ["tinyint", "smallint", "mediumint", "integer", "int", "bigint", "year"],
#     float: ["float", "double"],
#     Decimal: ["decimal(", "numeric("],
#     bool: ["boolean", "bool"],
#     datetime: ["datetime"], date: ["date"],
#     time: ["timestamp", "time"],
#     tuple: ["enum("], set: ["set("],
# }
PY_TYPES = {
    "varchar(": str, "char(": str, "tinytext": str,
    "text": str, "mediumtext": str, "longtext": str,
    "tinyint": int, "smallint": int, "mediumint": int,
    "integer": int, "int": int, "bigint": int, "year": int,
    "float": float, "double": float,
    "decimal(": Decimal, "numeric(": Decimal,
    "boolean": bool, "bool": bool,
    "datetime": datetime, "date": date,
    "timestamp": time, "time": time,
    "enum(": tuple, "set(": set
}
STANDARD_FIELD = {"datatype": 'text', "nullable": True, "default": None, "extra": ''}

class Keys:
    def __init__(self,
        primary: str | list[str] = '',
        foreign: dict[str, tuple[str, str]] = {},
        unique: str | list[str] = ''
    ):
        self._primary: ColumnName | list[ColumnName] = None
        self._foreign: dict[ColumnName, tuple[TableName, ColumnName]] = {}
        self._unique: ColumnName | list[ColumnName] = None

        if primary:
            self.primary = primary
        if foreign:
            self.foreign = foreign
        if unique:
            self.unique = unique

    def __bool__(self):
        return bool(self.all)

    def __str__(self):
        return str(self.all)

    def __repr__(self):
        repr_strings = []
        if self.primary:
            repr_strings.append(f"{self.primary=}"[5:])
        if self.foreign:
            repr_strings.append(f"{self.foreign=}"[5:])
        if self.unique:
            repr_strings.append(f"{self.unique=}"[5:])

        return f"Keys({",\n     ".join(repr_strings)})"

    def __eq__(self, other: typing.Self | dict[str, typing.Any]) -> bool:
        return self.all == other

    def _check_key(self, key: str | list[str], fk: bool = False) -> None:
        if not isinstance(key, str if fk else (str, list)):
            if fk:
                raise TypeError("Nøglen skal være et kolonnenavn som tekststreng.")
            else:
                raise TypeError("Nøglen skal enten være et kolonnenavn som tekststreng eller en liste af ditto.")
        if not key:
            raise ValueError("Nøglen må ikke være tom.")
        if fk or not isinstance(key, list):
            key = [key]
        for k in key:
            if ';' in key or '%' in key or '`' in key or "--" in key:
                raise ValueError("Ulovligt input.")

    @property
    def primary(self):
        if self._primary is None or not self._primary:
            return None
        return self._primary

    @primary.setter
    def primary(self, key: str):
        try:
            self._check_key(key)
        except Exception as err:
            print("Ugyldig nøgle.", err)
        else:
            self._primary = key

    @primary.deleter
    def primary(self):
        self._primary = None

    @property
    def foreign(self):
        if not self._foreign:
            return None
        return self._foreign

    @foreign.setter
    def foreign(self, key: dict[str, tuple[str, str]]):
        if not isinstance(key, dict):
            print(f"Ugyldig nøgle {key}. Nøglen skal være en dict.")
            return
        for k in key:
            try:
                self._check_key(k, fk=True)
            except Exception as err:
                print(f"Ugyldig nøgle {key}. {err}")
                continue
            # if not isinstance(k, str):
            #     print(f"Ugyldig nøgle {key}. Kolonnenavnet skal være en tekststreng.")
            #     continue
            # if not k:
            #     print(f"Ugyldig nøgle {key}. Kolonnenavnet må ikke være tomt.")
            #     continue
            ref = key[k]
            if not isinstance(ref, tuple):
                print(f"Ugyldig nøgle {key}. Referencen skal være en tuple.")
                continue
            if len(ref) != 2:
                print(f"Ugyldig nøgle {key}. Referencen må ikke indeholde mere eller mindre end to elementer: Et tabelnavn og et kolonnenavn.")
                continue
            for r in ref:
                if not isinstance(r, str):
                    print(f"Ugyldig nøgle {key}. Referencen må kun indeholde tekststrenge.")
                    break
                if not r:
                    print(f"Ugyldig nøgle {key}. Referencen må ikke indeholde tomme tekststrenge.")
                    break
            else:
                self._foreign.update(key)

    @foreign.deleter
    def foreign(self):
        self._foreign = {}

    @property
    def unique(self):
        if self._unique is None or not self._unique:
            return None
        return self._unique

    @unique.setter
    def unique(self, key: str):
        try:
            self._check_key(key)
        except Exception as err:
            print("Ugyldig nøgle.", err)
        else:
            self._unique = key

    @unique.deleter
    def unique(self):
        self._unique = None

    @property
    def all(self) -> dict[str, ColumnName | list[ColumnName] | ForeignKeys]:
        k = {}
        if self._primary is not None:
            k["primary"] = self._primary
        if self._foreign:
            k["foreign"] = self._foreign
        if self._unique is not None:
            k["unique"] = self._unique

        return k

class DataField:
    # BINARIES
    # bytes: / bytearray:
    # "bit(", "binary(", "varbinary(",
    # "tinyblob", "blob", "mediumblob", "longblob",

    def __init__(self,
        name: str,
        datatype: str = '',
        nullable: bool = True,
        *,
        default: typing.Any = None,
        extra: str = ''
    ) -> None:
        self._datatype: str = ''
        self._nullable: bool = True
        self._default: typing.Any = None
        self._extra: str = ''
        self._ptype: type

        self.name = name
        self.datatype = datatype
        self.nullable = nullable
        if default is not None:
            self.default = default
        if extra:
            self.extra = extra

    def __bool__(self):
        return bool(self.name) and bool(self.datatype)

    def __repr__(self):
        if not self.name or not self.datatype:
            return None
        col = {
            "datatype": self.datatype,
            "nullable": self.nullable
        }
        if self._default is not None:
            col["default"] = self.default
        if self.extra:
            col["extra"] = self.extra

        return repr(col)

    def _is_valid_string(self, name: str) -> bool:
        if not name or name is None:
            return False
        # Tjekker om forbudte tegn er i tekststrengen
        if any([';' in name, '%' in name, '`' in name, '.' in name, "--" in name]):
            return False
        return True

    def _is_valid_datatype(self, datatype: str) -> bool:
        if not self._is_valid_string:
            return False
        valid_types = PY_TYPES.keys()
        for valid_type in valid_types:
            if datatype.lower().startswith(valid_type):
                if valid_type.endswith('('):
                    # TODO: tjek om signed/unsigned passer til typen
                    # TODO: tjek om mængden af kommaer/tal passer til typen
                    if re.match(r"[a-z]+\([\d,]+\)( (un)?signed)?", datatype) is not None:
                        self._ptype = PY_TYPES[valid_type]
                        return True
                else:
                    self._ptype = PY_TYPES[valid_type]
                    return True
        return False

    def _is_valid_default(self, default: typing.Any) -> bool:
        # Hvis den angivne standardværdi er en tekststreng med forbudte tegn,
        # så returneres der med det samme
        if isinstance(default, str) and not self._is_valid_string(default):
            return False
        # Finder datatypenavn, hvis det er en variabel datatype
        # variable_type = self.datatype.find('(')
        # if variable_type > 0:
        #     type_index = self.datatype[0:variable_type+1]
        # else:
        #     type_index = self.datatype
        # # Hvis self.datatype ikke er i listen over gyldige datatyper pr. Python-type,
        # # så er den angivne standardværdi ikke gyldig
        # Tjekker om datatypen er den samme som defineret for kolonnen
        if type(default) != self._ptype:
            try:
                self._ptype(default)
            except:
                return False
        return True

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, input_name: str):
        if self._is_valid_string(input_name):
            self._name = input_name
        else:
            print(f"Ugyldigt kolonnenavn ({input_name}).")

    @property
    def datatype(self):
        if self._datatype:
            return self._datatype
        else:
            return "varchar(255)"
    
    @datatype.setter
    def datatype(self, input_datatype: str):
        if self._is_valid_datatype(input_datatype):
            self._datatype = input_datatype
        else:
            print(f"Ugyldig datatype ({input_datatype}) for kolonnen '{self.name}'.")

    @property
    def nullable(self):
        return self._nullable
    
    @nullable.setter
    def nullable(self, is_nullable: bool | typing.Any):
        if is_nullable:
            self._nullable = True
        if not is_nullable:
            self._nullable = False

    @nullable.deleter
    def nullable(self):
        self._nullable = True

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, input_default: typing.Any):
        if self.extra:
            print(f"En standardværdi ({input_default}) kan ikke defineres, da kolonnen '{self.name}' er indstillet som AUTO_INCREMENT.")
            return
        if self._is_valid_default(input_default):
            self._default = self._ptype(input_default)
        else:
            print(f"Den angivne standardværdi ({input_default}) passer ikke til den oplyste datatype for kolonnen '{self.name}' ({self.datatype}).")

    @default.deleter
    def default(self):
        self._default = None

    @property
    def extra(self):
        return self._extra
    
    @extra.setter
    def extra(self, ex: str):
        if self.default is not None:
            print(f"Kolonnen '{self.name}' kan ikke sættes som AUTO_INCREMENT, da en standardværdi ({self.default}) er defineret.")
            return
        if "auto" in ex.lower():
            self._extra = "AUTO_INCREMENT"

    @extra.deleter
    def extra(self):
        self.extra = ''

Header = typing.NewType("Header", dict[ColumnName, DataField])
"""
:param Header:
:type Header: dict[ColumnName, DataField]
"""

class InterTable:
    def __init__(self,
        name: TableName,
        header: Header,
        keys: Keys = Keys(),
        data: DataList = deque()
    ):
        self.name: TableName = name
        self.header: Header = header
        self.keys: Keys = keys
        self.data: DataList = []
        for entry in data:
            self.__iadd__(entry)

    def __repr__(self) -> dict[str, TableName | Header | Keys | DataList]:
        return repr({"name": self.name, "header": self.header, "keys": self.keys.all, "data": self.data})

    def __len__(self) -> int:
        # Længden af objektet findes altid ud fra DataList
        return len(self.data)

    @property
    def length(self) -> int:
        # Længden af objektet findes ud fra antal rækker data i DataList
        return self.__len__()

    @property
    def width(self) -> int:
        # 'Bredden' af objektet findes ud fra antal kolonner i Header
        return len(self.header)

    @property
    def size(self) -> tuple[int, int]:
        """
        En tuple indeholdende bredden (antal kolonner) og længden (antal rækker) for tabellen.

        :rtype: tuple[int, int]
        """
        return (self.width, len(self.data))

    def __iter__(self) -> typing.Iterator:
        # Der itereres altid over DataList
        return iter(self.data)

    def __getitem__(self, loc: ColumnName | int | slice) -> DataEntry | list[DataEntry] | tuple[typing.Any]:
        # Tekststrenge indekserer kolonnenavne
        if isinstance(loc, str):
            if loc not in self.header:
                raise KeyError(f"Kolonnen '{loc}' findes ikke i tabellen '{self.name}'.")
            primary = self.keys.primary
            if primary and isinstance(primary, str):
                return {val[primary]: val[loc] for val in self.data}
            return tuple(val[loc] for val in self.data)
        # Heltalt indekserer en enkelt række
        elif isinstance(loc, int):
            if loc >= len(self.data) or loc < -len(self.data):
                raise IndexError(f"Rækkeindekset (i={loc}) er uden for rækkevidde.")
            return self.data[loc]
        # Slices indekserer flere rækker
        elif isinstance(loc, slice):
            return self.data[loc]
        else:
            raise LookupError("Denne værdi kan ikke bruges til indeksering. Brug kolonnenavne for kolonner og heltal (eller slices) for rækker.")

    def __delitem__(self, loc: ColumnName | int | slice) -> None:
        # TODO: Skriv try-except-blokke
        # Tekststrenge indekserer kolonnenavne
        if isinstance(loc, str) and loc in self.header:
            self.remove_column(loc)
        # Heltal indekserer en enkelt række
        elif isinstance(loc, int) and loc < len(self.data) and loc >= -len(self.data):
            self.remove_row(loc)
        # Slices indekserer flere rækker
        elif isinstance(loc, slice):
            self.remove_row(loc)

    def __add__(self, other: DataEntry | typing.Self) -> typing.Self:
        if isinstance(other, dict):
            if self._validate_entry(other, new=True):
                copy = deepcopy(self)
                copy.data.append(other)
                return copy
        elif isinstance(other, type(self)):
            print("Joins er ikke implementeret endnu.")
            return deepcopy(self)

    def __iadd__(self, other: DataEntry | typing.Self) -> typing.Self:
        if isinstance(other, dict):
            if self._validate_entry(other, new=True):
                self.data.append(other)
                return self
        elif isinstance(other, type(self)):
            print("Joins er ikke implementeret endnu.")
            return self

    def __lshift__(self, other: DataField) -> typing.Self:
        if isinstance(other, DataField):
            self.header = {other.name: other, **self.header}
            for row, entry in enumerate(self.data):
                self.data[row] = {other.name: row+1, **entry}
            return self

    def __matmul__(self, other: tuple[DataField, str, dict[typing.Any, typing.Any]]) -> typing.Self:
        column, reference, mapping = other
        self.header[column.name] = column
        for entry in self.data:
            entry[column.name] = mapping[entry[reference]]
        return self

    # add row(s) x + y __add__
    # remove row(s) x - y __sub__
    # add column x * y __mul__
    # add column w/ reference x @ y __matmul__
    # remove column % __mod__

    # join x & y __and__
    # where x | y __matmul__

    # reverse order (ud fra indbygget id-kolonne) -x __neg__
    # pivot ~x __invert__

    #  __setitem__

    def _validate_entry(self, data: DataEntry, *, new: bool = True) -> bool:
        # Tjekker om entry er dict
        if not isinstance(data, dict):
            raise TypeError("En række indsat i tabellen skal være en dict.")
        # Tjekker om entry har samme antal kolonner som header
        if len(data) > self.width:
            raise IndexError(f"Rækken indeholder flere kolonner end tabellen ({len(data)} > {self.width}).")
        # Tjekker om kun kolonner defineret i headeren angives
        for col in data:
            if col not in self.header:
                raise KeyError(f"Der findes ingen kolonne med navnet '{col}' i tabellen '{self.name}'.")

        # Validerer værdi for hver kolonne
        for column in self.header:
            if not self._validate_value(data, self.header[column], new=new):
                break
        else:
            # Hvis alle tests bestås, er rækken gyldig
            return True

    def _validate_value(self, data: DataEntry, column: DataField, *, new: bool = True) -> bool:
        col_name = column.name
        col_type = column._ptype
        # Tjekker om værdi mangler
        if col_name not in data or (row_val := data[col_name]) is None:
            # Tjekker om standardværdi skal indsættes
            # TODO: Tjek også for auto-increment her
            if column.default is not None:
                data[col_name] = column.default
                return True
            # Tjekker om kolonne er nullable
            elif not column.nullable:
                raise ValueError(f"Ingen værdi angivet for kolonnen '{col_name}', som ikke er nullable.")
        else:
            # Tjekker om datatypen matcher med definitionen i headeren
            if type(row_val) != col_type:
                try:
                    # TODO: Find en måde brugeren kan indsætte egne formater på
                    if col_type == bool:
                        new_val = col_type(int(row_val))
                    elif col_type == date:
                        split_date = row_val.split('/')
                        new_val = col_type(int(split_date[2]), int(split_date[1]), int(split_date[0]))
                    elif col_type == Decimal:
                        new_val = col_type(row_val).quantize(Decimal("1.00"))
                    else:
                        new_val = col_type(row_val)
                except:
                    if isinstance(row_val, str) and row_val.lower() == "null":
                        new_val = None
                    else:
                        raise TypeError(f"Værdien ({row_val}) passer ikke til datatypen for kolonnen '{col_name}' ({column.datatype}).")
                finally:
                    data[col_name] = new_val
            # Tjekker om en række med identisk værdi i unikke kolonner findes
            # TODO: Tjek for dubletter blandt multicols
            if new and col_name in (self.keys.primary, self.keys.unique):
                if data[col_name] in self[col_name]:
                    raise ValueError(f"Der findes allerede en række med værdien ({col_name}={row_val}). Kolonnen '{col_name}' må kun indeholde unikke værdier.")
        return True

    def pop(self, times: int) -> DataEntry:
        pass

    def change_type(self, column: ColumnName, new_type: str) -> None:
        # Den nye datatype sættes
        col = self.header[column]
        col.datatype = new_type
        # Værdien i hver række castes til den nye tilsvarende Python-type
        for entry in self.data:
            self._validate_entry(entry, new=False)

    def rename(self, old: ColumnName, new: ColumnName) -> None:
        pass

    def refresh(self) -> None:
        for col in self.header:
            self.change_type(col, self.header[col].datatype)

    def remove_row(self, rows: int | slice) -> None:
        # Hvis et heltal bruges, fjernes kun den ene række med det id
        if isinstance(rows, int):
            self.data = [row for index, row in enumerate(self.data) if index != rows]
        # Hvis slicing bruges, fjernes rækker med id, der omfattes af slicet
        elif isinstance(rows, slice):
            self.data = [row for index, row in enumerate(self.data) if index not in range(len(self.data))[rows]]

    def remove_column(self, *columns: str) -> None:
        for column in columns:
            # HEADER
            # Kolonnens DataField fjernes fra headeren
            if column in self.header:
                self.header.pop(column)
            # KEYS
            # Hvis kolonnen var del af primary key, fjernes primary key
            if self.keys.primary is not None:
                if self.keys.primary == column or column in self.keys.primary:
                    del self.keys.primary
            # Hvis kolonnen var en foreign key, fjernes denne foreign key
            if self.keys.foreign is not None:
                if column in self.keys.foreign:
                    self.keys.foreign.pop(column)
            # Hvis kolonnen var del af en unique key, fjernes denne unique key
            if self.keys.unique is not None:
                if self.keys.unique == column:
                    del self.keys.unique
                elif column in self.keys.unique:
                    self.keys.unique.remove(column)
                    # Hvis der kun er en unique key tilbage,
                    # føres denne ud af listen for at stå selv
                    if len(self.keys.unique) == 1:
                        self.keys.unique = self.keys.unique[0]
            # Kolonnen fjernes i hver række i DataList
            for entry in self.data:
                if column in entry:
                    entry.pop(column)

if __name__ == "__main__":
    pass