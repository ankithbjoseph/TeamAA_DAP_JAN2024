# importing the required libraries.
from dagster import op, Out, In, get_dagster_logger, job
from pymongo import MongoClient, errors
import openmeteo_requests
import requests_cache
import pandas as pd
import os
from retry_requests import retry
from sqlalchemy import create_engine, text, inspect as sa_inspect
from functools import reduce
from dagster_pandas import PandasColumn, create_dagster_pandas_dataframe_type

log = get_dagster_logger()

cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


def _get_env(name: str, default: str | None = None, required: bool = False) -> str:
    val = os.getenv(name, default)
    if required and (val is None or val == ""):
        raise RuntimeError(f"Environment variable {name} is required but not set")
    return val


postgres_user     = _get_env("POSTGRES_USER", required=True)
postgres_password = _get_env("POSTGRES_PASSWORD", required=True)
postgres_host     = _get_env("POSTGRES_HOST", "postgres")
postgres_port     = _get_env("POSTGRES_PORT", "5432")
postgres_db       = _get_env("POSTGRES_DB_APP", "projectdb")
postgres_connect  = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

mongo_user     = _get_env("MONGO_INITDB_ROOT_USERNAME", required=True)
mongo_password = _get_env("MONGO_INITDB_ROOT_PASSWORD", required=True)
mongo_host     = _get_env("MONGO_HOST", "mongodb")
mongo_port     = _get_env("MONGO_PORT", "27017")
mongo_connect  = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}"

# ── Single source of truth for location / date configuration ──────────────────
CONFIG = {
    "latitude":   53.3331,
    "longitude":  -6.2489,
    "start_date": "2023-01-01",
    "end_date":   "2023-12-31",
}

# Drop footfall columns that are missing more than this fraction of values
MAX_NULL_COLUMN_RATIO = 0.8


# ── Shared helpers ────────────────────────────────────────────────────────────
def _fetch_hourly_dataframe(url: str, params: dict, variable_names: list[str]) -> pd.DataFrame:
    """Call the Open-Meteo API and return a DataFrame with one column per variable."""
    responses = openmeteo.weather_api(url, params=params)
    hourly = responses[0].Hourly()
    data: dict = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="right",
        )
    }
    for i, name in enumerate(variable_names):
        data[name] = hourly.Variables(i).ValuesAsNumpy()
    return pd.DataFrame(data=data)


def _mongo_insert_records(collection, records: list[dict]) -> int:
    """Insert records into MongoDB, skipping duplicates. Returns the duplicate count."""
    duplicate_count = 0
    for record in records:
        try:
            collection.insert_one(record)
        except errors.DuplicateKeyError:
            duplicate_count += 1
    return duplicate_count


def _filter_to_year(df: pd.DataFrame, start: str, end_exclusive: str) -> pd.DataFrame:
    """Filter a DataFrame with a 'date' column to [start, end_exclusive)."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["_id"]  = df["_id"].astype(int)
    return df[(df["date"] >= start) & (df["date"] < end_exclusive)]


def _clean_footfall(df: pd.DataFrame) -> pd.DataFrame:
    """Drop columns with >MAX_NULL_COLUMN_RATIO missing values and fill remaining nulls."""
    df = df.copy()
    df["_id"] = df["_id"].astype(int)
    missing_pct  = df.isna().sum() / len(df)
    cols_to_drop = missing_pct[missing_pct > MAX_NULL_COLUMN_RATIO].index
    return df.drop(columns=cols_to_drop).fillna(0)


# ── Extract ops ───────────────────────────────────────────────────────────────
@op(out=Out(bool))
def extract_weather() -> bool:
    """Fetches hourly weather data from Open-Meteo archive and inserts into MongoDB."""
    variable_names = [
        "temperature_2m", "relative_humidity_2m", "dew_point_2m",
        "apparent_temperature", "precipitation", "rain", "snowfall",
        "cloud_cover", "wind_speed_10m", "wind_direction_10m", "sunshine_duration",
    ]
    params = {
        "latitude":   CONFIG["latitude"],
        "longitude":  CONFIG["longitude"],
        "start_date": CONFIG["start_date"],
        "end_date":   CONFIG["end_date"],
        "hourly":     variable_names,
        "timeformat": "unixtime",
        "timezone":   "Europe/London",
    }
    try:
        df      = _fetch_hourly_dataframe(
            "https://archive-api.open-meteo.com/v1/archive", params, variable_names
        )
        records = df.to_dict("records")
        for r in records:
            r["_id"] = str(int(r["date"].timestamp()))

        with MongoClient(mongo_connect) as client:
            dup_count = _mongo_insert_records(
                client["projectdb_mongo"]["weather_collection"], records
            )

        if dup_count > 0:
            log.warning(f"Weather: {dup_count} duplicate records skipped")
        return True
    except Exception as e:
        log.error(f"Weather extraction failed: {e}")
        return False


@op(out=Out(bool))
def extract_aqi() -> bool:
    """Fetches hourly AQI data from Open-Meteo air-quality API and inserts into MongoDB."""
    variable_names = [
        "pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide",
        "dust", "european_aqi", "european_aqi_pm2_5", "european_aqi_pm10",
        "european_aqi_nitrogen_dioxide", "european_aqi_ozone", "european_aqi_sulphur_dioxide",
    ]
    params = {
        "latitude":   CONFIG["latitude"],
        "longitude":  CONFIG["longitude"],
        "start_date": CONFIG["start_date"],
        "end_date":   CONFIG["end_date"],
        "hourly":     variable_names,
        "timeformat": "unixtime",
        "timezone":   "Europe/London",
    }
    try:
        df      = _fetch_hourly_dataframe(
            "https://air-quality-api.open-meteo.com/v1/air-quality", params, variable_names
        )
        records = df.to_dict("records")
        for r in records:
            r["_id"] = str(int(r["date"].timestamp()))

        with MongoClient(mongo_connect) as client:
            dup_count = _mongo_insert_records(
                client["projectdb_mongo"]["aqi_collection"], records
            )

        if dup_count > 0:
            log.warning(f"AQI: {dup_count} duplicate records skipped")
        return True
    except Exception as e:
        log.error(f"AQI extraction failed: {e}")
        return False


@op(out=Out(bool))
def extract_footfall() -> bool:
    """Loads footfall data from footfall.csv and inserts into MongoDB."""
    try:
        try:
            footfall_df = pd.read_csv("footfall.csv")
        except FileNotFoundError as e:
            log.error(f"footfall.csv not found: {e}")
            return False

        records = footfall_df.to_dict("records")
        for r in records:
            r["_id"] = str(int(
                pd.to_datetime(r["Time"], format="%d/%m/%Y %H:%M").timestamp()
            ))

        with MongoClient(mongo_connect) as client:
            dup_count = _mongo_insert_records(
                client["projectdb_mongo"]["footfall_collection"], records
            )

        if dup_count > 0:
            log.warning(f"Footfall: {dup_count} duplicate records skipped")
        return True
    except Exception as e:
        log.error(f"Footfall extraction failed: {e}")
        return False


# ── Dagster type definitions ───────────────────────────────────────────────────
WeatherDataFrame = create_dagster_pandas_dataframe_type(
    name="WeatherDataFrame",
    columns=[
        PandasColumn.integer_column(name="_id", non_nullable=True),
        PandasColumn.datetime_column(name="date", non_nullable=True),
        PandasColumn.float_column(name="temperature_2m", non_nullable=True),
        PandasColumn.float_column(name="relative_humidity_2m", non_nullable=True),
        PandasColumn.float_column(name="dew_point_2m", non_nullable=True),
        PandasColumn.float_column(name="apparent_temperature", non_nullable=True),
        PandasColumn.float_column(name="precipitation", non_nullable=True),
        PandasColumn.float_column(name="rain", non_nullable=True),
        PandasColumn.float_column(name="snowfall", non_nullable=True),
        PandasColumn.float_column(name="cloud_cover", non_nullable=True),
        PandasColumn.float_column(name="wind_speed_10m", non_nullable=True),
        PandasColumn.float_column(name="wind_direction_10m", non_nullable=True),
        PandasColumn.float_column(name="sunshine_duration", non_nullable=True),
    ],
)

AqiDataFrame = create_dagster_pandas_dataframe_type(
    name="AqiDataFrame",
    columns=[
        PandasColumn.integer_column(name="_id", non_nullable=True),
        PandasColumn.datetime_column(name="date", non_nullable=True),
        PandasColumn.float_column(name="pm10", non_nullable=True),
        PandasColumn.float_column(name="pm2_5", non_nullable=True),
        PandasColumn.float_column(name="carbon_monoxide", non_nullable=True),
        PandasColumn.float_column(name="nitrogen_dioxide", non_nullable=True),
        PandasColumn.float_column(name="sulphur_dioxide", non_nullable=True),
        PandasColumn.float_column(name="dust", non_nullable=True),
        PandasColumn.float_column(name="european_aqi", non_nullable=True),
        PandasColumn.float_column(name="european_aqi_pm2_5", non_nullable=True),
        PandasColumn.float_column(name="european_aqi_pm10", non_nullable=True),
        PandasColumn.float_column(name="european_aqi_nitrogen_dioxide", non_nullable=True),
        PandasColumn.float_column(name="european_aqi_ozone", non_nullable=True),
        PandasColumn.float_column(name="european_aqi_sulphur_dioxide", non_nullable=True),
    ],
)

# No Dagster type validation for footfall — column schema varies by available locations


# ── Transform ops ──────────────────────────────────────────────────────────────
@op(ins={"start": In(bool)}, out=Out(WeatherDataFrame))
def transform_weather(start) -> pd.DataFrame:
    """Retrieves weather data from MongoDB and filters to 2023."""
    with MongoClient(mongo_connect) as client:
        weather_df = pd.DataFrame(
            list(client["projectdb_mongo"]["weather_collection"].find({}))
        )
    return _filter_to_year(weather_df, CONFIG["start_date"], "2024-01-01")


@op(ins={"start": In(bool)}, out=Out(AqiDataFrame))
def transform_aqi(start) -> pd.DataFrame:
    """Retrieves AQI data from MongoDB and filters to 2023."""
    with MongoClient(mongo_connect) as client:
        aqi_df = pd.DataFrame(
            list(client["projectdb_mongo"]["aqi_collection"].find({}))
        )
    return _filter_to_year(aqi_df, CONFIG["start_date"], "2024-01-01")


@op(ins={"start": In(bool)})
def transform_footfall(start) -> pd.DataFrame:
    """Retrieves footfall data from MongoDB and drops columns with >80% nulls."""
    with MongoClient(mongo_connect) as client:
        footfall_df = pd.DataFrame(
            list(client["projectdb_mongo"]["footfall_collection"].find({}))
        )
    return _clean_footfall(footfall_df)


@op(
    ins={
        "weather_df":  In(WeatherDataFrame),
        "aqi_df":      In(AqiDataFrame),
        "footfall_df": In(pd.DataFrame),
    },
    out=Out(pd.DataFrame),
)
def join_data(weather_df, aqi_df, footfall_df) -> pd.DataFrame:
    """Merges weather, AQI, and footfall DataFrames on the shared _id key."""
    aqi_df = aqi_df.drop("date", axis=1)
    footfall_df = footfall_df[
        [
            "_id",
            "Aston Quay/Fitzgeralds",
            "Baggot st lower/Wilton tce inbound",
            "Baggot st upper/Mespil rd/Bank",
            "Capel st/Mary street",
            "College Green/Bank Of Ireland",
            "College st/Westmoreland st",
            "D'olier st/Burgh Quay",
            "Dame Street/Londis",
            "Grafton st/Monsoon",
            "Grafton Street / Nassau Street / Suffolk Street",
            "Grafton Street/CompuB",
            "Grand Canal st upp/Clanwilliam place",
            "Grand Canal st upp/Clanwilliam place/Google",
            "Mary st/Jervis st",
            "North Wall Quay/Samuel Beckett bridge East",
            "North Wall Quay/Samuel Beckett bridge West",
            "O'Connell st/Princes st North",
            "Phibsborough Rd/Enniskerry Road",
            "Richmond st south/Portabello Harbour inbound",
            "Richmond st south/Portabello Harbour outbound",
        ]
    ]
    dfs = [weather_df, aqi_df, footfall_df]
    return reduce(
        lambda left, right: pd.merge(left, right, on="_id", how="inner"), dfs
    )


@op(ins={"merged_df": In(pd.DataFrame)}, out=Out(bool))
def load_data(merged_df) -> bool:
    """Loads the merged DataFrame into PostgreSQL, truncating stale rows without dropping the table."""
    postgres_engine = create_engine(postgres_connect)
    try:
        insp = sa_inspect(postgres_engine)
        if insp.has_table("weather_aqi_footfall", schema="public"):
            with postgres_engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE public.weather_aqi_footfall"))

        with postgres_engine.connect() as conn:
            row_count = merged_df.to_sql(
                name="weather_aqi_footfall",
                schema="public",
                con=conn,
                index=False,
                if_exists="append",
            )
            conn.commit()

        log.info(f"{row_count} records loaded into weather_aqi_footfall")
        return True
    except Exception as e:
        log.error(f"Load failed: {e}")
        return False


@job()
def etl():
    load_data(
        join_data(
            transform_weather(extract_weather()),
            transform_aqi(extract_aqi()),
            transform_footfall(extract_footfall()),
        )
    )
