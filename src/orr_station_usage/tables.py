"""Readers for ORR tables 1410 and 1415."""

from __future__ import annotations

import pathlib
import re

import pandas as pd

# One row per station for one year.
TABLE_1410_COLUMNS = [
    "year",
    "crs",
    "nlc",
    "station",
    "region",
    "entries_exits",
    "entries_exits_full",
    "entries_exits_reduced",
    "entries_exits_season",
    "interchanges",
]

# One row per station per year.
TABLE_1415_COLUMNS = [
    "year",
    "crs",
    "nlc",
    "station",
    "region",
    "entries_exits",
    "interchanges",
    "series_break",
]

# Each output column, and the first source column it is read from: the
# first whose lower-cased name contains every word in one of the
# tuples. The current year's columns come before last year's in every
# release, so the first match is the right one.
_1410_RULES: dict[str, list[tuple[str, ...]]] = {
    "station": [("station name",)],
    "crs": [("tlc",)],
    "nlc": [("nlc",)],
    "region": [("region",)],
    "entries_exits": [("entries", "total"), ("entries", "all tickets")],
    "entries_exits_full": [("entries", "full")],
    "entries_exits_reduced": [("entries", "reduc")],
    "entries_exits_season": [("entries", "season")],
    "interchanges": [("interchange",)],
}

# "Apr 2024 to Mar 2025", "April 2024 to March 2025" or "2024-25".
_YEAR = re.compile(r"\bApr\w*\s+(\d{4})\s+to\s+Mar\w*\s+\d{4}|\b(\d{4})-(\d{2})\b")


def _year_label(start: int) -> str:
    return f"{start}-{(start + 1) % 100:02d}"


def _find_year(*texts: str) -> str | None:
    for text in texts:
        match = _YEAR.search(text)
        if match:
            return _year_label(int(match.group(1) or match.group(2)))
    return None


def _number(series: pd.Series) -> pd.Series:
    """Floats; ``[x]``, ``[z]``, ``:`` and blanks become NaN."""
    text = series.astype(str).str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(text, errors="coerce")


def _sheets(path: pathlib.Path) -> dict[str, pd.DataFrame]:
    """Every sheet as raw cells; a CSV is one sheet."""
    if path.suffix.lower() == ".csv":
        return {path.stem: pd.read_csv(path, header=None, dtype=str, encoding="utf-8-sig")}
    if path.suffix.lower() == ".ods":
        return pd.read_excel(path, sheet_name=None, header=None, dtype=str, engine="odf")
    return pd.read_excel(path, sheet_name=None, header=None, dtype=str)


def _with_header(raw: pd.DataFrame) -> pd.DataFrame | None:
    """The table below its header row, or ``None`` if it has none.

    The header is the first row with a cell reading "Station name".
    Line breaks in header cells become spaces.
    """
    first = raw.apply(lambda col: col.astype(str).str.strip().str.lower() == "station name")
    rows = first.any(axis=1)
    if not rows.any():
        return None
    at = int(rows.to_numpy().argmax())
    header = [re.sub(r"\s+", " ", str(c)).strip() for c in raw.iloc[at]]
    table = raw.iloc[at + 1 :].set_axis(header, axis=1).reset_index(drop=True)
    return table.dropna(how="all")


def _column(table: pd.DataFrame, rules: list[tuple[str, ...]]) -> pd.Series | None:
    names = [str(c).lower() for c in table.columns]
    for words in rules:
        for i, name in enumerate(names):
            if all(w in name for w in words):
                return table.iloc[:, i]
    return None


def _text(series: pd.Series | None) -> pd.Series | None:
    """Trimmed text; markers such as ``[z]`` and blanks become NA."""
    if series is None:
        return None
    text = series.astype(str).str.strip()
    return text.mask(text.str.fullmatch(r"\[\w\]|nan|"), pd.NA)


def _codes(series: pd.Series | None) -> pd.Series | None:
    if series is None:
        return None
    text = series.astype(str).str.strip().str.upper()
    return text.where(text.str.fullmatch(r"[A-Z0-9]+") & (text != "NAN"))


def read_table_1410(path: pathlib.Path | str, year: str | None = None) -> pd.DataFrame:
    """One year of table 1410, one row per station.

    Reads the ODS, XLSX or CSV that the ORR publishes, from 2019-20 on.
    The year (``"2024-25"``) is found in the column names, the cover
    sheet or the filename; pass ``year`` if none of those has it. Ticket
    type columns missing from a release are left empty.
    """
    path = pathlib.Path(path)
    sheets = _sheets(path)
    tables = [(name, t) for name, raw in sheets.items() if (t := _with_header(raw)) is not None]
    data = [t for name, t in tables if _column(t, _1410_RULES["entries_exits"]) is not None]
    if not data:
        raise ValueError(f"{path.name}: no sheet with a station name and entries column")
    table = data[0]

    cover = " ".join(
        str(v) for raw in sheets.values() if raw.shape[1] for v in raw.iloc[:3, 0].dropna()
    )
    year = year or _find_year(" ".join(map(str, table.columns)), cover, path.name)
    if year is None:
        raise ValueError(f"{path.name}: cannot tell which year this is; pass year=")

    out = pd.DataFrame(index=table.index)
    for column, rules in _1410_RULES.items():
        values = _column(table, rules)
        out[column] = values if values is not None else pd.NA
    out["crs"] = _codes(out["crs"])
    out["nlc"] = _codes(out["nlc"])
    for column in TABLE_1410_COLUMNS[5:]:
        out[column] = _number(out[column])
    out["station"] = _text(out["station"])
    out["region"] = _text(out["region"])
    out["year"] = year
    out = out[out["crs"].notna() | out["entries_exits"].notna()]
    return out[TABLE_1410_COLUMNS].reset_index(drop=True)


def _melt_1415(table: pd.DataFrame, value: str) -> pd.DataFrame:
    keys = {
        "station": _text(_column(table, [("station name",)])),
        "crs": _codes(_column(table, [("tlc",)])),
        "nlc": _codes(_column(table, [("nlc",)])),
        "region": _text(_column(table, [("region",)])),
    }
    frame = pd.DataFrame({k: v for k, v in keys.items() if v is not None})
    years = {c: _find_year(str(c)) for c in table.columns}
    year_columns = [c for c, y in years.items() if y]
    long = pd.concat([frame, table[year_columns]], axis=1).melt(
        id_vars=list(frame.columns), var_name="label", value_name=value
    )
    long["year"] = long["label"].map(years)
    long["series_break"] = long["label"].astype(str).str.contains(r"\[b\]")
    long[value] = _number(long[value])
    return long.drop(columns="label")


def read_table_1415(path: pathlib.Path | str) -> pd.DataFrame:
    """Table 1415's time series, one row per station per year.

    Entries and exits come from sheet 1415a and interchanges from
    1415b. Years the ORR marks ``[x]`` (no estimate) or ``[z]`` (station
    not open) are NaN. ``series_break`` is true for a year the ORR marks
    ``[b]``: its method changed, so compare across it with care.
    """
    path = pathlib.Path(path)
    tables = {}
    for name, raw in _sheets(path).items():
        table = _with_header(raw)
        if table is not None and name.lower().startswith(("1415a", "1415b")):
            tables[name.lower()[:5]] = table
    if "1415a" not in tables:
        raise ValueError(f"{path.name}: no 1415a sheet")

    entries = _melt_1415(tables["1415a"], "entries_exits")
    if "1415b" in tables:
        # Closed stations have no codes, so match on the name.
        changes = _melt_1415(tables["1415b"], "interchanges")
        entries = entries.merge(
            changes[["station", "year", "interchanges"]],
            on=["station", "year"],
            how="left",
            validate="one_to_one",
        )
    else:
        entries["interchanges"] = float("nan")
    entries = entries.sort_values(["crs", "year"], kind="stable")
    return entries[TABLE_1415_COLUMNS].reset_index(drop=True)


def read(path: pathlib.Path | str) -> pd.DataFrame:
    """Read either table, telling them apart by their sheet names."""
    path = pathlib.Path(path)
    if path.suffix.lower() != ".csv":
        names = pd.ExcelFile(path, engine="odf" if path.suffix.lower() == ".ods" else None)
        if any(str(s).lower().startswith("1415a") for s in names.sheet_names):
            return read_table_1415(path)
    return read_table_1410(path)
