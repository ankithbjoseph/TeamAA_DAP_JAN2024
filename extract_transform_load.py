from dagster import op, Out, In, get_dagster_logger, job
from pymongo import MongoClient, errors
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from sqlalchemy import create_engine
from functools import reduce
from dagster_pandas import PandasColumn, create_dagster_pandas_dataframe_type

log = get_dagster_logger()
# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)
postgres_connect = "postgresql://dap:dap@postgres_database:5432/projectdb"
mongo_connect = "mongodb://dap:dap@mongodb_database"
# postgres_connect = "postgresql://dap:dap@127.0.0.1:5432/projectdb"
# mongo_connect = "mongodb://dap:dap@127.0.0.1"


@op(out=Out(bool))
def extract_weather() -> bool:
    result = True
    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 53.3331,
        "longitude": -6.2489,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "dew_point_2m",
            "apparent_temperature",
            "precipitation",
            "rain",
            "snowfall",
            "weather_code",
            "cloud_cover",
            "wind_speed_10m",
            "wind_direction_10m",
            "is_day",
            "sunshine_duration",
        ],
        "timeformat": "unixtime",
        "timezone": "Europe/London",
    }
    try:
        client = MongoClient(mongo_connect)
        projectdb_mongo = client["projectdb_mongo"]

        weather_collection = projectdb_mongo["weather_collection"]

        responses = openmeteo.weather_api(url, params=params)

        response = responses[0]
        print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
        print(f"Elevation {response.Elevation()} m asl")
        print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
        print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
        hourly_dew_point_2m = hourly.Variables(2).ValuesAsNumpy()
        hourly_apparent_temperature = hourly.Variables(3).ValuesAsNumpy()
        hourly_precipitation = hourly.Variables(4).ValuesAsNumpy()
        hourly_rain = hourly.Variables(5).ValuesAsNumpy()
        hourly_snowfall = hourly.Variables(6).ValuesAsNumpy()
        hourly_weather_code = hourly.Variables(7).ValuesAsNumpy()
        hourly_cloud_cover = hourly.Variables(8).ValuesAsNumpy()
        hourly_wind_speed_10m = hourly.Variables(9).ValuesAsNumpy()
        hourly_wind_direction_10m = hourly.Variables(10).ValuesAsNumpy()
        hourly_is_day = hourly.Variables(11).ValuesAsNumpy()
        hourly_sunshine_duration = hourly.Variables(12).ValuesAsNumpy()

        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="right",
            )
        }
        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
        hourly_data["dew_point_2m"] = hourly_dew_point_2m
        hourly_data["apparent_temperature"] = hourly_apparent_temperature
        hourly_data["precipitation"] = hourly_precipitation
        hourly_data["rain"] = hourly_rain
        hourly_data["snowfall"] = hourly_snowfall
        hourly_data["weather_code"] = hourly_weather_code
        hourly_data["cloud_cover"] = hourly_cloud_cover
        hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
        hourly_data["wind_direction_10m"] = hourly_wind_direction_10m
        hourly_data["is_day"] = hourly_is_day
        hourly_data["sunshine_duration"] = hourly_sunshine_duration

        hourly_dataframe = pd.DataFrame(data=hourly_data)
        hourly_dataframe_dict = hourly_dataframe.to_dict("records")

        duplicate_count = 0
        for data in hourly_dataframe_dict:
            try:
                data["_id"] = f"{(int(data['date'].timestamp()))}"
                weather_collection.insert_one(data)

            except errors.DuplicateKeyError:
                duplicate_count += 1
        if duplicate_count > 0:
            log.warning(f"Total duplicate data not inserted: {duplicate_count}")

    except Exception as e:
        log.error(f"Error: {e}")
        result = False

    # Return a Boolean indicating success or failure
    return result


@op(out=Out(bool))
def extract_aqi() -> bool:
    result = True
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": 53.3331,
        "longitude": -6.2489,
        "hourly": [
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "dust",
            "european_aqi",
            "european_aqi_pm2_5",
            "european_aqi_pm10",
            "european_aqi_nitrogen_dioxide",
            "european_aqi_ozone",
            "european_aqi_sulphur_dioxide",
        ],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "timeformat": "unixtime",
        "timezone": "Europe/London",
    }
    try:
        client = MongoClient(mongo_connect)
        projectdb_mongo = client["projectdb_mongo"]

        aqi_collection = projectdb_mongo["aqi_collection"]

        responses = openmeteo.weather_api(url, params=params)

        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]
        print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
        print(f"Elevation {response.Elevation()} m asl")
        print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
        print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

        # Process hourly data. The order of variables needs to be the same as requested.
        hourly = response.Hourly()
        hourly_pm10 = hourly.Variables(0).ValuesAsNumpy()
        hourly_pm2_5 = hourly.Variables(1).ValuesAsNumpy()
        hourly_carbon_monoxide = hourly.Variables(2).ValuesAsNumpy()
        hourly_nitrogen_dioxide = hourly.Variables(3).ValuesAsNumpy()
        hourly_sulphur_dioxide = hourly.Variables(4).ValuesAsNumpy()
        hourly_dust = hourly.Variables(5).ValuesAsNumpy()
        hourly_european_aqi = hourly.Variables(6).ValuesAsNumpy()
        hourly_european_aqi_pm2_5 = hourly.Variables(7).ValuesAsNumpy()
        hourly_european_aqi_pm10 = hourly.Variables(8).ValuesAsNumpy()
        hourly_european_aqi_nitrogen_dioxide = hourly.Variables(9).ValuesAsNumpy()
        hourly_european_aqi_ozone = hourly.Variables(10).ValuesAsNumpy()
        hourly_european_aqi_sulphur_dioxide = hourly.Variables(11).ValuesAsNumpy()

        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="right",
            )
        }
        hourly_data["pm10"] = hourly_pm10
        hourly_data["pm2_5"] = hourly_pm2_5
        hourly_data["carbon_monoxide"] = hourly_carbon_monoxide
        hourly_data["nitrogen_dioxide"] = hourly_nitrogen_dioxide
        hourly_data["sulphur_dioxide"] = hourly_sulphur_dioxide
        hourly_data["dust"] = hourly_dust
        hourly_data["european_aqi"] = hourly_european_aqi
        hourly_data["european_aqi_pm2_5"] = hourly_european_aqi_pm2_5
        hourly_data["european_aqi_pm10"] = hourly_european_aqi_pm10
        hourly_data["european_aqi_nitrogen_dioxide"] = (
            hourly_european_aqi_nitrogen_dioxide
        )
        hourly_data["european_aqi_ozone"] = hourly_european_aqi_ozone
        hourly_data["european_aqi_sulphur_dioxide"] = (
            hourly_european_aqi_sulphur_dioxide
        )

        hourly_dataframe = pd.DataFrame(data=hourly_data)
        hourly_dataframe_dict = hourly_dataframe.to_dict("records")

        duplicate_count = 0
        for data in hourly_dataframe_dict:
            try:
                data["_id"] = f"{int(data['date'].timestamp())}"
                aqi_collection.insert_one(data)

            except errors.DuplicateKeyError:
                duplicate_count += 1
        if duplicate_count > 0:
            log.warning(f"Total duplicate data not inserted: {duplicate_count}")

    except Exception as e:
        log.error(f"Error: {e}")
        result = False

    # Return a Boolean indicating success or failure
    return result


@op(out=Out(bool))
def extract_footfall() -> bool:
    result = True
    try:
        client = MongoClient(mongo_connect)
        projectdb_mongo = client["projectdb_mongo"]
        footfall_collection = projectdb_mongo["footfall_collection"]

        footfall_csv = "footfall.csv"
        try:
            footfall_df = pd.read_csv(footfall_csv)
            footfall_dict = footfall_df.to_dict("records")
        except Exception as e:
            log.error(f"Failed to read data from CSV file. \n {e}")

        duplicate_count = 0
        for data in footfall_dict:
            try:
                data["_id"] = str(
                    int(
                        (
                            pd.to_datetime(data["Time"], format="%d/%m/%Y %H:%M")
                        ).timestamp()
                    )
                )
                footfall_collection.insert_one(data)

            except errors.DuplicateKeyError:
                duplicate_count += 1
        if duplicate_count > 0:
            log.warning(f"Total duplicate data not inserted: {duplicate_count}")

    except Exception as e:
        log.error(f"Error: {e}")
        result = False

    # Return a Boolean indicating success or failure
    return result


WeatherDataFrame = create_dagster_pandas_dataframe_type(
    name="WeatherDataFrame",
    columns=[
        PandasColumn.integer_column(
            name="_id",
            non_nullable=True,  # specify that the column shouldn't contain NAs
        ),
        PandasColumn.datetime_column(
            name="date",
            non_nullable=True,  # specify that the column shouldn't contain NAs
        ),
        PandasColumn.float_column(name="temperature_2m", non_nullable=True),
        PandasColumn.float_column(name="relative_humidity_2m", non_nullable=True),
        PandasColumn.float_column(name="dew_point_2m", non_nullable=True),
        PandasColumn.float_column(name="apparent_temperature", non_nullable=True),
        PandasColumn.float_column(name="precipitation", non_nullable=True),
        PandasColumn.float_column(name="rain", non_nullable=True),
        PandasColumn.float_column(name="snowfall", non_nullable=True),
        PandasColumn.float_column(name="weather_code", non_nullable=True),
        PandasColumn.float_column(name="cloud_cover", non_nullable=True),
        PandasColumn.float_column(name="wind_speed_10m", non_nullable=True),
        PandasColumn.float_column(name="wind_direction_10m", non_nullable=True),
        PandasColumn.float_column(name="is_day", non_nullable=True),
        PandasColumn.float_column(name="sunshine_duration", non_nullable=True),
    ],
)
AqiDataFrame = create_dagster_pandas_dataframe_type(
    name="AqiDataFr",
    columns=[
        PandasColumn.integer_column(
            name="_id",
            non_nullable=True,  # specify that the column shouldn't contain NAs
        ),
        PandasColumn.datetime_column(
            name="date",
            non_nullable=True,  # specify that the column shouldn't contain NAs
        ),
        PandasColumn.float_column(name="pm10", non_nullable=True),
        PandasColumn.float_column(name="pm2_5", non_nullable=True),
        PandasColumn.float_column(name="carbon_monoxide", non_nullable=True),
        PandasColumn.float_column(name="nitrogen_dioxide", non_nullable=True),
        PandasColumn.float_column(name="sulphur_dioxide", non_nullable=True),
        PandasColumn.float_column(name="dust", non_nullable=True),
        PandasColumn.float_column(name="european_aqi", non_nullable=True),
        PandasColumn.float_column(name="european_aqi_pm2_5", non_nullable=True),
        PandasColumn.float_column(name="european_aqi_pm10", non_nullable=True),
        PandasColumn.float_column(
            name="european_aqi_nitrogen_dioxide", non_nullable=True
        ),
        PandasColumn.float_column(name="european_aqi_ozone", non_nullable=True),
        PandasColumn.float_column(
            name="european_aqi_sulphur_dioxide", non_nullable=True
        ),
    ],
)


@op(ins={"start": In(bool)}, out=Out(WeatherDataFrame))
def transform_weather(start) -> pd.DataFrame:
    client = MongoClient(mongo_connect)
    projectdb_mongo = client["projectdb_mongo"]

    weather_collection = projectdb_mongo["weather_collection"]

    weather_df = pd.DataFrame(list(weather_collection.find({})))

    weather_df["date"] = pd.to_datetime(weather_df["date"])
    weather_df["_id"] = weather_df["_id"].astype(int)

    weather_df = weather_df[
        (weather_df["date"] >= "2023-01-01") & (weather_df["date"] < "2024-01-01")
    ]
    return weather_df


@op(ins={"start": In(bool)}, out=Out(AqiDataFrame))
def transform_aqi(start) -> pd.DataFrame:
    client = MongoClient(mongo_connect)
    projectdb_mongo = client["projectdb_mongo"]

    aqi_collection = projectdb_mongo["aqi_collection"]

    aqi_df = pd.DataFrame(list(aqi_collection.find({})))

    aqi_df["date"] = pd.to_datetime(aqi_df["date"])
    aqi_df["_id"] = aqi_df["_id"].astype(int)
    # Filtering data from 2023-01-01 to 2023-12-31
    aqi_df = aqi_df[(aqi_df["date"] >= "2023-01-01") & (aqi_df["date"] < "2024-01-01")]

    return aqi_df


@op()
def transform_footfall(start) -> pd.DataFrame:
    client = MongoClient(mongo_connect)
    projectdb_mongo = client["projectdb_mongo"]
    aqi_collection = projectdb_mongo["footfall_collection"]
    footfall_df = pd.DataFrame(list(aqi_collection.find({})))
    footfall_df["_id"] = footfall_df["_id"].astype(int)
    # Cleaning data removing all variables with more than 80% Null Values
    threshold = 0.8
    missing_percentage = footfall_df.isna().sum() / len(footfall_df)
    columns_to_drop = missing_percentage[missing_percentage > threshold].index
    footfall_df = footfall_df.drop(columns=columns_to_drop)
    footfall_df = footfall_df.fillna(0)
    return footfall_df


@op(
    ins={
        "weather_df": In(WeatherDataFrame),
        "aqi_df": In(AqiDataFrame),
        "footfall_df": In(pd.DataFrame),
    },
    out=Out(pd.DataFrame),
)
def join_data(weather_df, aqi_df, footfall_df) -> pd.DataFrame:
    aqi_df = aqi_df.drop("date", axis=1)
    dfs = [weather_df, aqi_df, footfall_df]
    merged_df = reduce(
        lambda left, right: pd.merge(left, right, on="_id", how="inner"), dfs
    )

    return merged_df


@op()
def load_data(merged_df) -> bool:
    postgres_engine = create_engine(postgres_connect)

    with postgres_engine.connect() as conn:
        row_count = merged_df.to_sql(
            name="weather_aqi_footfall",
            schema="public",
            con=conn,
            index=False,
            if_exists="replace",
        )
        log.info("{} records loaded".format(row_count))
        return True


@job()
def etl():
    load_data(
        join_data(
            transform_weather(extract_weather()),
            transform_aqi(extract_aqi()),
            transform_footfall(extract_footfall()),
        )
    )
