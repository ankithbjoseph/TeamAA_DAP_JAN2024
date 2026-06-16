"""
Unit tests for extract_transform_load.py.

All tests operate on in-memory DataFrames or mock objects — no live
database or network connection is required.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from pymongo import errors

from extract_transform_load import (
    _mongo_insert_records,
    _filter_to_year,
    _clean_footfall,
    join_data,
    CONFIG,
    MAX_NULL_COLUMN_RATIO,
)


# ── _mongo_insert_records ─────────────────────────────────────────────────────

class TestMongoInsertRecords:
    def test_all_new_records_inserted(self):
        collection = MagicMock()
        records = [{"_id": "1", "val": 10}, {"_id": "2", "val": 20}]
        dup_count = _mongo_insert_records(collection, records)
        assert dup_count == 0
        assert collection.insert_one.call_count == 2

    def test_duplicate_key_counted_and_skipped(self):
        collection = MagicMock()
        collection.insert_one.side_effect = [
            None,
            errors.DuplicateKeyError("dup"),
            None,
        ]
        records = [{"_id": "1"}, {"_id": "2"}, {"_id": "3"}]
        dup_count = _mongo_insert_records(collection, records)
        assert dup_count == 1
        assert collection.insert_one.call_count == 3

    def test_all_duplicates(self):
        collection = MagicMock()
        collection.insert_one.side_effect = errors.DuplicateKeyError("dup")
        records = [{"_id": "1"}, {"_id": "2"}]
        dup_count = _mongo_insert_records(collection, records)
        assert dup_count == 2

    def test_empty_records(self):
        collection = MagicMock()
        dup_count = _mongo_insert_records(collection, [])
        assert dup_count == 0
        collection.insert_one.assert_not_called()


# ── _filter_to_year ────────────────────────────────────────────────────────────

class TestFilterToYear:
    def _make_df(self):
        return pd.DataFrame({
            "_id": ["1674000000", "1680000000", "1705000000"],
            "date": pd.to_datetime(["2023-01-18", "2023-03-28", "2024-01-12"]),
            "value": [1.0, 2.0, 3.0],
        })

    def test_excludes_rows_outside_range(self):
        df     = self._make_df()
        result = _filter_to_year(df, "2023-01-01", "2024-01-01")
        assert len(result) == 2
        assert all(result["date"] < pd.Timestamp("2024-01-01"))

    def test_converts_id_to_int(self):
        df     = self._make_df()
        result = _filter_to_year(df, "2023-01-01", "2024-01-01")
        assert result["_id"].dtype == int

    def test_does_not_mutate_input(self):
        df     = self._make_df()
        before = df["_id"].tolist()
        _filter_to_year(df, "2023-01-01", "2024-01-01")
        assert df["_id"].tolist() == before  # original unchanged


# ── _clean_footfall ────────────────────────────────────────────────────────────

class TestCleanFootfall:
    def test_drops_column_above_null_ratio(self):
        df = pd.DataFrame({
            "_id": ["1", "2", "3"],
            "good": [1.0, 2.0, 3.0],
            "sparse": [None, None, None],  # 100% null → dropped
        })
        result = _clean_footfall(df)
        assert "sparse" not in result.columns
        assert "good" in result.columns

    def test_keeps_column_below_null_ratio(self):
        df = pd.DataFrame({
            "_id": ["1", "2", "3", "4"],
            "half_null": [1.0, None, 3.0, None],  # 50% < 80% → kept
        })
        result = _clean_footfall(df)
        assert "half_null" in result.columns

    def test_fills_remaining_nulls_with_zero(self):
        df = pd.DataFrame({
            "_id": ["1", "2"],
            "loc_a": [5.0, None],
        })
        result = _clean_footfall(df)
        assert result["loc_a"].isna().sum() == 0
        assert result.loc[result["_id"] == 2, "loc_a"].iloc[0] == 0.0

    def test_converts_id_to_int(self):
        df = pd.DataFrame({"_id": ["100", "200"], "val": [1.0, 2.0]})
        result = _clean_footfall(df)
        assert result["_id"].dtype == int

    def test_does_not_mutate_input(self):
        df     = pd.DataFrame({"_id": ["1"], "x": [None]})
        before = df.copy()
        _clean_footfall(df)
        pd.testing.assert_frame_equal(df, before)

    def test_max_null_ratio_constant_is_sensible(self):
        assert 0 < MAX_NULL_COLUMN_RATIO < 1


# ── join_data ──────────────────────────────────────────────────────────────────

def _base_weather():
    return pd.DataFrame({
        "_id": [1, 2],
        "date": pd.to_datetime(["2023-01-01", "2023-01-02"]),
        "temperature_2m": [5.0, 6.0],
        "relative_humidity_2m": [80.0, 75.0],
        "dew_point_2m": [3.0, 4.0],
        "apparent_temperature": [3.0, 4.0],
        "precipitation": [0.0, 0.0],
        "rain": [0.0, 0.0],
        "snowfall": [0.0, 0.0],
        "cloud_cover": [90.0, 85.0],
        "wind_speed_10m": [10.0, 12.0],
        "wind_direction_10m": [180.0, 200.0],
        "sunshine_duration": [0.0, 100.0],
    })


def _base_aqi():
    return pd.DataFrame({
        "_id": [1, 2],
        "date": pd.to_datetime(["2023-01-01", "2023-01-02"]),
        "pm10": [10.0, 11.0],
        "pm2_5": [5.0, 5.5],
        "carbon_monoxide": [200.0, 210.0],
        "nitrogen_dioxide": [15.0, 16.0],
        "sulphur_dioxide": [2.0, 2.1],
        "dust": [0.1, 0.2],
        "european_aqi": [30.0, 32.0],
        "european_aqi_pm2_5": [20.0, 21.0],
        "european_aqi_pm10": [15.0, 16.0],
        "european_aqi_nitrogen_dioxide": [10.0, 11.0],
        "european_aqi_ozone": [25.0, 26.0],
        "european_aqi_sulphur_dioxide": [5.0, 5.5],
    })


def _base_footfall():
    cols = {
        "_id": [1, 2],
        "Aston Quay/Fitzgeralds": [100, 200],
        "Baggot st lower/Wilton tce inbound": [50, 60],
        "Baggot st upper/Mespil rd/Bank": [70, 80],
        "Capel st/Mary street": [30, 40],
        "College Green/Bank Of Ireland": [150, 160],
        "College st/Westmoreland st": [90, 100],
        "D'olier st/Burgh Quay": [80, 90],
        "Dame Street/Londis": [110, 120],
        "Grafton st/Monsoon": [200, 220],
        "Grafton Street / Nassau Street / Suffolk Street": [180, 190],
        "Grafton Street/CompuB": [130, 140],
        "Grand Canal st upp/Clanwilliam place": [60, 70],
        "Grand Canal st upp/Clanwilliam place/Google": [40, 50],
        "Mary st/Jervis st": [120, 130],
        "North Wall Quay/Samuel Beckett bridge East": [30, 35],
        "North Wall Quay/Samuel Beckett bridge West": [25, 30],
        "O'Connell st/Princes st North": [250, 260],
        "Phibsborough Rd/Enniskerry Road": [40, 45],
        "Richmond st south/Portabello Harbour inbound": [55, 60],
        "Richmond st south/Portabello Harbour outbound": [50, 55],
    }
    return pd.DataFrame(cols)


class TestJoinData:
    def test_output_contains_all_source_columns(self):
        result = join_data(_base_weather(), _base_aqi(), _base_footfall())
        assert "temperature_2m" in result.columns
        assert "pm10" in result.columns
        assert "Grafton st/Monsoon" in result.columns

    def test_row_count_matches_inner_join(self):
        result = join_data(_base_weather(), _base_aqi(), _base_footfall())
        assert len(result) == 2

    def test_inner_join_drops_unmatched_ids(self):
        footfall = _base_footfall()[_base_footfall()["_id"] == 1]
        result   = join_data(_base_weather(), _base_aqi(), footfall)
        assert len(result) == 1
        assert result["_id"].iloc[0] == 1

    def test_aqi_date_column_removed(self):
        result = join_data(_base_weather(), _base_aqi(), _base_footfall())
        # After the merge, there should be exactly one 'date' column from weather
        assert result.columns.tolist().count("date") == 1


# ── CONFIG ─────────────────────────────────────────────────────────────────────

class TestConfig:
    def test_required_keys_present(self):
        for key in ("latitude", "longitude", "start_date", "end_date"):
            assert key in CONFIG, f"CONFIG missing key: {key}"

    def test_dublin_coordinates(self):
        assert 53.0 < CONFIG["latitude"] < 54.0
        assert -7.0 < CONFIG["longitude"] < -6.0

    def test_date_range_is_2023(self):
        assert CONFIG["start_date"] == "2023-01-01"
        assert CONFIG["end_date"]   == "2023-12-31"
