from __future__ import annotations

import pathlib

import pytest

from orr_station_usage import (
    TABLE_1410_COLUMNS,
    TABLE_1415_COLUMNS,
    cli,
    read,
    read_table_1410,
    read_table_1415,
)


class TestTable1410:
    def test_latest_layout(self, latest_1410: pathlib.Path) -> None:
        table = read_table_1410(latest_1410)
        assert list(table.columns) == TABLE_1410_COLUMNS
        leeds = table.set_index("crs").loc["LDS"]
        assert leeds["year"] == "2024-25"
        assert leeds["entries_exits"] == 27_309_508
        assert leeds["entries_exits_season"] == 3_092_466
        assert leeds["nlc"] == "8487"

    def test_markers_are_missing(self, latest_1410: pathlib.Path) -> None:
        table = read_table_1410(latest_1410).set_index("crs")
        assert table.loc["ABC", "interchanges"] != table.loc["ABC", "interchanges"]  # NaN

    def test_old_layout_takes_this_years_total(self, old_1410: pathlib.Path) -> None:
        table = read_table_1410(old_1410)
        assert table["year"].tolist() == ["2019-20"]
        assert table["entries_exits"].tolist() == [31_020_744]
        assert table["interchanges"].tolist() == [2_958_091]

    def test_year_can_be_given(self, latest_1410: pathlib.Path, tmp_path: pathlib.Path) -> None:
        assert read_table_1410(latest_1410, year="2030-31")["year"].iloc[0] == "2030-31"

    def test_csv_without_a_year_asks_for_one(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "export.csv"
        path.write_text("Station name,Entries and exits - All tickets,TLC\nLeeds,5,LDS\n")
        with pytest.raises(ValueError, match="year="):
            read_table_1410(path)
        assert read_table_1410(path, year="2024-25")["entries_exits"].tolist() == [5]


class TestTable1415:
    def test_one_row_per_station_year(self, series_1415: pathlib.Path) -> None:
        table = read_table_1415(series_1415)
        assert list(table.columns) == TABLE_1415_COLUMNS
        assert len(table) == 3 * 3
        leeds = table[table["crs"] == "LDS"].set_index("year")
        assert leeds.loc["2023-24", "entries_exits"] == 24_891_386
        assert leeds.loc["2023-24", "interchanges"] == 2_684_197

    def test_series_break(self, series_1415: pathlib.Path) -> None:
        table = read_table_1415(series_1415)
        assert set(table.loc[table["series_break"], "year"]) == {"2022-23"}

    def test_closed_station_keeps_its_name(self, series_1415: pathlib.Path) -> None:
        closed = read_table_1415(series_1415).query("station == 'Closed Halt'")
        assert closed["crs"].isna().all()
        assert closed["region"].isna().all()
        assert closed["entries_exits"].tolist()[0] == 100

    def test_read_tells_the_tables_apart(
        self, series_1415: pathlib.Path, latest_1410: pathlib.Path
    ) -> None:
        assert "series_break" in read(series_1415).columns
        assert "entries_exits_full" in read(latest_1410).columns


class TestCli:
    def test_station(self, series_1415: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert cli.main([str(series_1415), "-s", "lds"]) == 0
        out = capsys.readouterr().out
        assert "24,891,386" in out
        assert "NTN" not in out

    def test_writes_csv(
        self, series_1415: pathlib.Path, latest_1410: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        out = tmp_path / "usage.csv"
        assert cli.main([str(series_1415), str(latest_1410), "-o", str(out)]) == 0
        text = out.read_text()
        assert "2024-25" in text
        assert "2021-22" in text

    def test_unknown_station(
        self, series_1415: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert cli.main([str(series_1415), "-s", "ZZZ"]) == 1

    def test_missing_file(self, tmp_path: pathlib.Path) -> None:
        assert cli.main([str(tmp_path / "nope.ods")]) == 1
