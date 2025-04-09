import typing
import hashlib
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
    def __init__(self,
        name: str,
        datatype: str = '',
        nullable: bool = True,
        default: typing.Any = None,
        extra: str = ''
    ) -> None:
        self._name = name
        self._datatype: str = ''
        self._nullable: bool = True
        self._default: typing.Any = None
        self._extra: str = ''

        self.name = name
        self.datatype = datatype
        if nullable:
            self.nullable = nullable
        if default is not None:
            self.default = default
        if extra:
            self.extra = extra

    def _is_valid_name(name: str) -> bool:
        if not name or name is None:
            return False
        if any(';' in name, '%' in name, '`' in name, "--" in name):
            return False

    def _is_valid_datatype(datatype: str) -> bool:
        pass

    def _is_valid_default(default: typing.Any) -> bool:
        pass

    @property
    def name(self):
        return self._name
    
    @property
    def extra(self):
        if self._extra:
            return self._extra
    
    @extra.setter
    def extra(self, ex: str):
        if "auto" in ex.lower():
            self._extra = "AUTO_INCREMENT"

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
DataField = typing.NewType("DataField", dict[str, ColumnName | str | bool | typing.Any])
"""
:param DataField:
:type DataField: dict{str, str | bool | typing.Any}
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
