import re
import typing
from decimal import Decimal
from datetime import date, datetime, time
from dataclasses import dataclass

STANDARD_FIELD = {"type": '', "nullable": True, "default": None, "extra": ''}

class Keys:
    def __init__(self,
        primary: str | list[str] = '',
        foreign: dict[str, tuple[str, str]] = {},
        unique: str | list[str] = ''
    ):
        self._primary: ColumnName = None
        self._foreign: dict[ColumnName, tuple[TableName, ColumnName]] = {}
        self._unique: list[ColumnName] = None

        if primary:
            self.primary = primary
        if foreign:
            self.foreign = foreign
        if unique:
            self.unique = unique

    def __str__(self):
        return str(self.keys())

    def __repr__(self):
        repr_strings = []
        if self.primary:
            repr_strings.append(f"{self.primary=}"[5:])
        if self.foreign:
            repr_strings.append(f"{self.foreign=}"[5:])
        if self.unique:
            repr_strings.append(f"{self.unique=}"[5:])

        return f"Keys({",\n     ".join(repr_strings)})"

    def __eq__(self, other) -> bool:
        return self.keys() == other

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

    def keys(self):
        k = {}
        if self._primary is not None:
            k["primary"] = self._primary
        if self._foreign:
            k["foreign"] = self._foreign
        if self._unique is not None:
            k["unique"] = self._unique

        return k

class DataField:
    VALID_TYPES = {
        str: ["varchar(", "char(", "tinytext", "text", "mediumtext", "longtext"],
        int: ["tinyint", "smallint", "mediumint", "int", "integer", "bigint", "year"],
        float: ["float", "double"],
        Decimal: ["decimal(", "numeric("],
        bool: ["bool", "boolean"],
        date: ["date"],
        time: ["time", "timestamp"],
        datetime: ["datetime"],
        tuple: ["enum("],
        set: ["set("],
    }
    # BINARIES
    # bytes: / bytearray:
    # "bit(", "binary(", "varbinary(",
    # "tinyblob", "blob", "mediumblob", "longblob",

    def __init__(self,
        name: str,
        datatype: str = '',
        nullable: bool = True,
        default: typing.Any = None,
        extra: str = ''
    ) -> None:
        self._datatype: str = ''
        self._nullable: bool = True
        self._default: typing.Any = None
        self._extra: str = ''

        self.name = name
        self.datatype = datatype
        self.nullable = nullable
        if default is not None:
            self.default = default
        if extra:
            self.extra = extra

    def __repr__(self):
        if not self.name or not self.datatype:
            return None
        col = {
            self.name: {
                "type": self.datatype,
                "nullable": self.nullable
            }
        }
        if self._default is not None:
            col[self.name]["default"] = self.default
        if self.extra:
            col[self.name]["extra"] = self.extra

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
        valid_types = [subtype for datatype in DataField.VALID_TYPES.values() for subtype in datatype]
        for valid_type in valid_types:
            if datatype.lower().startswith(valid_type):
                if valid_type.endswith('('):
                    if re.match(r"[a-z]+\([\d,]+\)", datatype) is not None:
                        return True
                else:
                    return True
        return False

    def _is_valid_default(self, default: typing.Any) -> bool:
        # Hvis den angivne standardværdi er en tekststreng med forbudte tegn,
        # så returneres der med det samme
        if isinstance(default, str) and not self._is_valid_string(default):
            return False
        # Finder datatypenavn, hvis det er en variabel datatype
        variable_type = self.datatype.find('(')
        if variable_type > 0:
            type_index = self.datatype[0:variable_type+1]
        else:
            type_index = self.datatype
        # Hvis self.datatype ikke er i listen over gyldige datatyper pr. Python-type,
        # så er den angivne standardværdi ikke gyldig
        if type_index not in self.VALID_TYPES[type(default)]:
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
            print("Ugyldigt kolonnenavn.")

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
            print("Ugyldig datatype for kolonnen.")

    @property
    def nullable(self):
        return self._nullable
    
    @nullable.setter
    def nullable(self, is_nullable: bool):
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
        if self._is_valid_default(input_default):
            self._default = input_default
        else:
            print("Den angivne standardværdi passer ikke til den oplyste datatype.")

    @default.deleter
    def default(self):
        self._default = None

    @property
    def extra(self):
        return self._extra
    
    @extra.setter
    def extra(self, ex: str):
        if "auto" in ex.lower():
            self._extra = "AUTO_INCREMENT"

    @extra.deleter
    def extra(self):
        self.extra = ''

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
# DataField = typing.NewType("DataField", dict[str, ColumnName | str | bool | typing.Any])
# """
# :param DataField:
# :type DataField: dict{str, str | bool | typing.Any}
# """
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
TableHeader = typing.NewType("TableHeader", dict[ColumnName, DataField])
"""
:param TableHeader:
:type TableHeader: dict[ColumnName, DataField]
"""
ForeignKeys = typing.NewType("ForeignKeys", dict[ColumnName, tuple[TableName, ColumnName]])
"""
:param ForeignKeys:
:type ForeignKeys: dict[Constraint, tuple[TableName, str]]
"""
ConstraintList = typing.NewType("ConstraintList", list[ColumnName])
"""
:param ConstraintList:
:type ConstraintList: list[ColumnName]
"""
# TableKeys = typing.NewType("TableKeys", dict[str, ColumnName | ConstraintList | ForeignKeys])
# """
# :param TableKeys:
# :type TableKeys: dict[str, ColumnName | ConstraintList | ForeignKeys]
# """
TableData = typing.NewType("TableData", list[DataEntry])
"""
:param TableData:
:type TableData: list[DataEntry]
"""
Table = typing.NewType("Table", dict[str, TableName | TableHeader | Keys | TableData])
"""
:param Table:
:type Table: dict[str, TableName | TableHeader | TableKeys | TableData]
"""

@dataclass(init=True)
class InterTable:
    name: TableName
    header: TableHeader
    keys: Keys
    data: TableData

    def __repr__(self):
        return repr({"name": self.name, "header": self.header, "keys": self.keys, "data": self.data})

if __name__ == "__main__":
    test = DataField("hest", "varchar(80)", False, "fadslkjaseseg")
    print(test)