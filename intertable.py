import typing

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
TableKeys = typing.NewType("TableKeys", dict[str, ColumnName | ConstraintList | ForeignKeys])
"""
:param TableKeys:
:type TableKeys: dict[str, ColumnName | ConstraintList | ForeignKeys]
"""
TableData = typing.NewType("TableData", list[DataEntry])
"""
:param TableData:
:type TableData: list[DataEntry]
"""
Table = typing.NewType("Table", dict[str, TableName | TableHeader | TableKeys | TableData])
"""
:param Table:
:type Table: dict[str, TableName | TableHeader | TableKeys | TableData]
"""