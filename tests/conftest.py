"""Small ODS files laid out like ORR's.

The real tables are free to download, but a test should not depend on
the ORR's website. These copy the parts the readers rely on: title rows
above the header, ``[x]`` and ``[z]`` markers, a ``[b]`` series break,
an empty leftover sheet, and the header wording of two releases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pytest

if TYPE_CHECKING:
    import pathlib


def _write(path: pathlib.Path, sheets: dict[str, list[list[object]]]) -> pathlib.Path:
    with pd.ExcelWriter(path, engine="odf") as writer:
        for name, rows in sheets.items():
            width = max((len(row) for row in rows), default=0)
            padded = [row + [None] * (width - len(row)) for row in rows]
            pd.DataFrame(padded).to_excel(writer, sheet_name=name, header=False, index=False)
    return path


TITLE = [["Table 1410: Passenger entries, exits and interchanges by station"], ["Notes"]]


@pytest.fixture
def latest_1410(tmp_path: pathlib.Path) -> pathlib.Path:
    """2024-25 layout: the year is only on the cover sheet."""
    header = [
        "Station name",
        "Entries and exits: Full price tickets",
        " Entries and exits: Reduced price tickets",
        "Entries and exits:Season tickets",
        "Entries and exits:All tickets",
        "Entries and exits:Rank",
        "Interchanges",
        "National Location Code (NLC)",
        "Three Letter Code\n(TLC)",
        "Region",
    ]
    rows = [
        [
            "Leeds",
            "7051004",
            "17166038",
            "3092466",
            "27309508",
            "8",
            "2877961",
            "8487",
            "LDS",
            "Yorkshire and The Humber",
        ],
        ["Altnabreac", "20", "4", "0", "24", "2589", "[x]", "9999", "ABC", "Scotland"],
    ]
    cover = [
        [
            "Table 1410: Passenger entries, exits and interchanges by station, Great "
            "Britain, annual data, April 2024 to March 2025"
        ]
    ]
    return _write(
        tmp_path / "table-1410.ods",
        {"Cover_sheet": cover, "1410_Entries_Exits_Interchanges": [*TITLE, [], header, *rows]},
    )


@pytest.fixture
def old_1410(tmp_path: pathlib.Path) -> pathlib.Path:
    """2019-20 layout: last year's total sits beside this year's."""
    header = [
        "Station Name",
        "2019-20 Entries & Exits_Full",
        "2019-20 Entries & Exits_Reduced",
        "2019-20 Entries & Exits_Season",
        "2019-20 Entries & Exits_TOTAL",
        "2018-19 Entries & Exits_TOTAL",
        "2019-20 Interchanges",
        "NLC",
        "TLC",
        "Region",
    ]
    rows = [["Leeds", "1", "2", "3", "31020744", "30837000", "2958091", "8487", "LDS", "Y"]]
    return _write(
        tmp_path / "estimates-of-station-usage-2019-20.ods",
        {"1410_Entries&Exits_Interchange": [*TITLE, [], [], header, *rows], "'file:///U:/x": []},
    )


@pytest.fixture
def series_1415(tmp_path: pathlib.Path) -> pathlib.Path:
    keys = [
        "Sort",
        "Station name",
        "Three Letter Code\n(TLC)",
        "National Location Code (NLC)",
        "Region",
    ]
    years = ["Apr 2021 to Mar 2022", "Apr 2022 to Mar 2023 [b]", "Apr 2023 to Mar 2024"]
    a = [
        *TITLE,
        [],
        [*keys, *years],
        ["1", "Leeds", "LDS", "8487", "Yorkshire", "19263472", "23964156", "24891386"],
        ["2", "Closed Halt", "[z]", "[z]", "[z]", "100", "[z]", "[z]"],
        ["3", "Newtown", "NTN", "1234", "Wales", "[x]", "500", "600"],
    ]
    b = [
        *TITLE,
        [],
        [*keys, *years],
        ["1", "Leeds", "LDS", "8487", "Yorkshire", "1797861", "2488509", "2684197"],
        ["2", "Closed Halt", "[z]", "[z]", "[z]", "0", "[z]", "[z]"],
        ["3", "Newtown", "NTN", "1234", "Wales", "[x]", "0", "0"],
    ]
    return _write(
        tmp_path / "table-1415.ods",
        {"Cover_sheet": [["Table 1415"]], "1415a_Entries_and_Exits": a, "1415b_Interchanges": b},
    )
