# orr-station-usage

[![PyPI](https://img.shields.io/pypi/v/orr-station-usage)](https://pypi.org/project/orr-station-usage/)
[![Python](https://img.shields.io/pypi/pyversions/orr-station-usage)](https://pypi.org/project/orr-station-usage/)
[![CI](https://github.com/rosedillon/orr-station-usage/actions/workflows/ci.yml/badge.svg)](https://github.com/rosedillon/orr-station-usage/actions/workflows/ci.yml)
[![Licence: GPL-3.0](https://img.shields.io/badge/licence-GPL--3.0-blue)](https://github.com/rosedillon/orr-station-usage/blob/main/LICENSE)

Read the Office of Rail and Road's estimates of station usage, the
number of people entering, leaving and changing trains at every station
in Great Britain each year, into tidy tables.

The ORR publishes two tables. Table 1410 covers the latest year, with a
split by ticket type. Table 1415 has every year since 1997-98. Both
come as ODS spreadsheets with title rows above the header and markers
such as `[x]` and `[z]` in place of numbers. Column names change from
one year's release to the next: the total is "2019-20 Entries &
Exits_TOTAL" in one release, "Apr 2021 to Mar 2022 Entries and exits -
All tickets" in another and "Entries and exits:All tickets" in the
latest. This package reads any of them into the same columns.

```python
from orr_station_usage import read_table_1410, read_table_1415

latest = read_table_1410("table-1410-passenger-entries-and-exits-and-interchanges-by-station.ods")
series = read_table_1415(
    "table-1415-time-series-of-passenger-entries-and-exits-and-interchanges-by-station.ods"
)
```

## Install

Python 3.11 or later.

```sh
pip install orr-station-usage
```

It depends on pandas, odfpy (for ODS) and openpyxl (for XLSX).

## Getting the data

Both tables are free to download, with no account, from the ORR's
[estimates of station usage](https://dataportal.orr.gov.uk/statistics/usage/estimates-of-station-usage/)
page. A new year is released each November or December. Older releases
of table 1410 are on the same page.

## Command line

One station's history from table 1415:

```console
$ orr-station-usage table-1415-...ods -s LDS
   year crs station  entries_exits  interchanges
...
2019-20 LDS   Leeds     31,020,744     2,958,091
2020-21 LDS   Leeds      5,853,754       544,590
2021-22 LDS   Leeds     19,263,472     1,797,861
2022-23 LDS   Leeds     23,964,156     2,488,509
2023-24 LDS   Leeds     24,891,386     2,684,197
2024-25 LDS   Leeds     27,309,508     2,877,961
```

Years before a station opened are left out of the printout. Headbolt
Lane opened in October 2023:

```console
$ orr-station-usage table-1415-...ods -s HBL
   year crs       station  entries_exits  interchanges
2023-24 HBL Headbolt Lane        410,906        15,154
2024-25 HBL Headbolt Lane      1,410,668        17,871
```

To combine several files into one CSV:

```console
$ orr-station-usage table-1415-...ods table-1410-*.ods -o usage.csv
Wrote 74,671 rows to usage.csv
```

Where table 1410 and 1415 both cover a year, the 1410 row is kept
because it has the ticket types.

## What comes back

`read_table_1410` gives one row per station:

| Column | |
|---|---|
| `year` | `"2024-25"`, April to March |
| `crs` | three-letter station code |
| `nlc` | 4-digit National Location Code, as in the fares feed |
| `station`, `region` | as published |
| `entries_exits` | entries plus exits, all tickets |
| `entries_exits_full`, `_reduced`, `_season` | by ticket type |
| `interchanges` | changes between trains at the station |

`read_table_1415` gives one row per station per year, with `year`,
`crs`, `nlc`, `station`, `region`, `entries_exits`, `interchanges` and
`series_break`.

The year of a table 1410 file is read from its column names, its cover
sheet or its filename. The CSV the ORR offers as an alternative has
none of those, so pass `year="2024-25"` (or `--year 2024-25`).

## Things to know about the numbers

- They are estimates, built mostly from ticket sales. A ticket to a
  group of stations (London Terminals, Manchester stations) is shared
  out among its members by a model, and travel on passes and some local
  smartcards is estimated separately. Read the ORR's quality and
  methodology report before relying on small differences.
- `series_break` is true for 2022-23, which the ORR marks `[b]` because
  the method changed that year. Compare across it with care.
- `[x]` (no estimate) and `[z]` (not applicable, usually because the
  station was not open) both become NaN. A station that has closed
  keeps its name in table 1415, but its code and region are `[z]` and
  come back empty.
- The two tables do not always agree. For 2024-25 they give the same
  entries and exits at every station, but table 1410 has no interchange
  figure for Altnabreac, Stanlow and Thornton or Teesside Airport where
  table 1415 gives 0.
- 2020-21 and 2021-22 are pandemic years. Leeds fell from 31.0 million
  to 5.9 million and has not yet returned to its 2019-20 level.

## Python API

| Name | |
|---|---|
| `read_table_1410(path, year=None)` | one year, one row per station |
| `read_table_1415(path)` | every year, one row per station per year |
| `read(path)` | either, told apart by sheet names |
| `TABLE_1410_COLUMNS`, `TABLE_1415_COLUMNS` | the output columns |

## Related packages

Part of a set of Python packages for Great Britain's open rail data:

- [bplan-geography](https://github.com/rosedillon/bplan-geography), minimum running times from Network Rail's BPLAN extract
- [cif-timetable](https://github.com/rosedillon/cif-timetable), calling points and trains per route from the Network Rail CIF timetable
- [hsp-client](https://github.com/rosedillon/hsp-client), how late UK trains actually ran, from the National Rail HSP API
- [rail-loading](https://github.com/rosedillon/rail-loading), UK train operators' passenger loading data in one schema
- [rsp-fares-feed](https://github.com/rosedillon/rsp-fares-feed), every fare between two stations, from the National Rail fares feed
- [tag-databook](https://github.com/rosedillon/tag-databook), DfT TAG Data Book appraisal values without opening Excel
- [track-distance](https://github.com/rosedillon/track-distance), station distances along the rails, from Network Rail's track model
- [rail-codes](https://github.com/rosedillon/rail-codes), TIPLOC, CRS, NLC and STANOX lookups from Network Rail's CORPUS

## Development

```sh
git clone https://github.com/rosedillon/orr-station-usage
cd orr-station-usage
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check . && mypy src
```

The tests build small ODS files laid out like the ORR's, so they run
without downloading anything.

## Licence

GPL-3.0. See
[LICENSE](https://github.com/rosedillon/orr-station-usage/blob/main/LICENSE).
The ORR's statistics are published under the Open Government Licence.
