"""Read the ORR's estimates of station usage into tidy tables.

The Office of Rail and Road publishes how many people enter, leave and
change trains at every station in Great Britain each year. Table 1410
has the latest year in detail and table 1415 has every year since
1997-98. Both come as ODS spreadsheets with title rows above the
header, markers such as ``[x]`` in place of numbers, and column names
that change from one year's release to the next::

    from orr_station_usage import read_table_1410, read_table_1415

    latest = read_table_1410("table-1410-...ods")
    series = read_table_1415("table-1415-...ods")
"""

from __future__ import annotations

from orr_station_usage.tables import (
    TABLE_1410_COLUMNS,
    TABLE_1415_COLUMNS,
    read,
    read_table_1410,
    read_table_1415,
)

__version__ = "0.1.0"

__all__ = [
    "TABLE_1410_COLUMNS",
    "TABLE_1415_COLUMNS",
    "read",
    "read_table_1410",
    "read_table_1415",
]
