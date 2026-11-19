"""Command-line interface."""

from __future__ import annotations

import argparse
import pathlib
import sys
import warnings
from typing import TYPE_CHECKING

import pandas as pd

from orr_station_usage.tables import read, read_table_1410

if TYPE_CHECKING:
    from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orr-station-usage",
        description=(
            "Read ORR tables 1410 and 1415 (estimates of station usage) into one "
            "tidy CSV, or print one station's figures."
        ),
    )
    parser.add_argument("files", nargs="+", type=pathlib.Path, metavar="FILE")
    parser.add_argument("-o", "--output", type=pathlib.Path, help="write a CSV here")
    parser.add_argument("-s", "--station", metavar="CRS", help="only this station")
    parser.add_argument("--year", help="year of a table 1410 file that does not say, e.g. 2024-25")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    frames = []
    for path in args.files:
        if not path.exists():
            print(f"error: {path} not found", file=sys.stderr)
            return 1
        # odfpy and openpyxl warn about styles ORR's files use.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                frames.append(read_table_1410(path, args.year) if args.year else read(path))
            except ValueError as error:
                print(f"error: {error}", file=sys.stderr)
                return 1
    # Where both tables cover a year, keep 1410's row: it has the
    # ticket types.
    frames.sort(key=lambda frame: "series_break" in frame.columns)
    table = pd.concat(frames, ignore_index=True)
    table = table.drop_duplicates(subset=["crs", "station", "year"], keep="first")
    table = table.sort_values(["crs", "year"], kind="stable", na_position="last")

    if args.station:
        table = table[table["crs"] == args.station.strip().upper()]
        if table.empty:
            print(f"no rows for {args.station.upper()}", file=sys.stderr)
            return 1

    if args.output:
        table.to_csv(args.output, index=False)
        print(f"Wrote {len(table):,} rows to {args.output}", file=sys.stderr)
    else:
        columns = ["year", "crs", "station", "entries_exits", "interchanges"]
        # Years before a station opened are all blank.
        table = table.dropna(how="all", subset=["entries_exits", "interchanges"])
        print(table[columns].to_string(index=False, float_format=lambda v: f"{v:,.0f}"))
    return 0
