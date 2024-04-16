import numpy as np
import pandas as pd
from cassandra.cluster import Cluster
from dagster import op, Out, In, get_dagster_logger
from dagster_pandas import PandasColumn, create_dagster_pandas_dataframe_type
from pymongo import MongoClient, errors
from sqlalchemy import create_engine, exc
from sqlalchemy.pool import NullPool
from sqlalchemy.types import *

postgres_connection_string = "postgresql://dap:dap@postgres_database:5432/flights"
mongo_connection_string = "mongodb://dap:dap@mongodb_database"
logger = get_dagster_logger()

FlightsDataFrame = create_dagster_pandas_dataframe_type(
    name="FlightsDataFrame",
    columns=[
        PandasColumn.datetime_column(
            name="date",
            non_nullable=True # specify that the column shouldn't contain NAs
        ),
        PandasColumn.string_column(
            name="origin.id",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="origin.city",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="origin.country",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="origin.iata_code",
            non_nullable=True    
        ),
        PandasColumn.float_column(
            name="origin.latitude",
            non_nullable=True
        ),
        PandasColumn.float_column(
            name="origin.longitude",
            non_nullable=True
        ),
        PandasColumn.float_column(
            name="origin.elevation",
            non_nullable=True
        ),
        PandasColumn.string_column(
            name="destination.id",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="destination.city",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="destination.country",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="destination.iata_code",
            non_nullable=True    
        ),
        PandasColumn.float_column(
            name="destination.latitude",
            non_nullable=True
        ),
        PandasColumn.float_column(
            name="destination.longitude",
            non_nullable=True
        ),
        PandasColumn.float_column(
            name="destination.elevation",
            non_nullable=True
        ),
        PandasColumn.string_column(
            name="aircraft.callsign",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="aircraft.name",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="aircraft.operator.name",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="aircraft.operator.callsign",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="aircraft.operator.iata_code",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="aircraft.operator.icao_code",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="aircraft.operator.country",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="aircraft.manufacturer",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="aircraft.model",
            non_nullable=True    
        ),
        PandasColumn.string_column(
            name="aircraft.manufacturer",
            non_nullable=True    
        ),
        PandasColumn.integer_column(
            name="aircraft.numberofengines",
            min_value=2, # specify that the column should contain whole numbers
            max_value=4, # between 2 and 4
            non_nullable=True
        ),
        PandasColumn.string_column(
            name="aircraft.enginetype",
            non_nullable=True
        ),
        PandasColumn.string_column(
            name="departure.scheduled",
            non_nullable=True
        ),
        PandasColumn.string_column(
            name="departure.actual",
            non_nullable=True
        ),
        PandasColumn.string_column(
            name="arrival.scheduled",
            non_nullable=True
        ),
        PandasColumn.string_column(
            name="arrival.actual",
            non_nullable=True
        )
    ]
)

WeatherDataFrame = create_dagster_pandas_dataframe_type(
    name="WeatherDataFrame",
    columns=[
        PandasColumn.datetime_column(
            name="datetime",
            non_nullable=True
        ),
        PandasColumn.numeric_column(
            name="pressure",
            min_value=920,
            max_value=1060,
            non_nullable=True
        ),
        PandasColumn.numeric_column(
            name="rain",
            min_value=0,
            max_value=20,
            non_nullable=True
        ),
        PandasColumn.integer_column(
            name="wind_direction",
            min_value=0,
            max_value=360,
            non_nullable=True
        ),
        PandasColumn.numeric_column(
            name="wind_speed",
            min_value=0,
            max_value=200,
            non_nullable=True
        )
    ]
)

@op(
    ins={"start": In(bool)},
    out=Out(WeatherDataFrame)
)

def transform_weather(start):
    
    # Connect to the Cassandra database
    cassandra = Cluster(["cassandra_database"])
    
    # Connect to the weather keyspace
    cassandra_session = cassandra.connect("weather")
    
    # Retrieve all rows in the weather table
    weather_df = pd.DataFrame(list(
        cassandra_session.execute("SELECT * FROM weather;")
    ))
    
    # Convert wind speed in knots to km/h
    weather_df["wind_speed"] = weather_df["wind_speed"] * 1.852
    
    # Return the transformed data frame
    return(weather_df)

@op(
    ins={"start": In(bool)},
    out=Out(FlightsDataFrame)
)

def transform_flights(start):
    
    # Connect to the MongoDB database
    client = MongoClient(mongo_connection_string)
    
    # Connect to the flights collection
    flights_db = client["flights"]
    
    # Retrieve the data from the collection, flatten it and
    # return a Pandas data frame
    flights_df = pd.json_normalize(list(flights_db.flights.find({})))
    
    # Create a dictionary with column names as the key and the object (string) 
    # type as the value. This will be used to specify data types for the
    # data frame. We will change some of these types later.
    flights_datatypes = dict(
        zip(flights_df.columns, [object]*len(flights_df.columns))
    )
    
    # Set date column to have the Numpy datetime64 datatype 
    #flights_datatypes["date"] = np.datetime64
    flights_datatypes["date"] = "datetime64[ns]"
    
    # Set columns to have the Numpy float64 datatype 
    for column in ["origin.latitude","origin.longitude","origin.elevation",
                   "destination.latitude","destination.longitude",
                   "destination.elevation"]:
        flights_datatypes[column] = np.float64
    
    # Set aircraft.numberofengines column to have the Numpy int64 datatype 
    flights_datatypes["aircraft.numberofengines"] = np.int64   
    
    # Use the flights_datatypes dictionary to set data types for the data frame
    flights_df = flights_df.astype(flights_datatypes)
    
    # Drop the _id column as we don't need it
    flights_df.drop(["_id"],axis=1,inplace=True)

    # Return the flights data frame    
    return flights_df

@op(
    ins={"flights_df": In(pd.DataFrame), "weather_df": In(WeatherDataFrame)},
    out=Out(pd.DataFrame)
)

def join(flights_df,weather_df) -> pd.DataFrame:
    
    # Join the two data frames
    merged_df = flights_df.merge(
        right=weather_df,
        how="left",
        left_on="date",
        right_on="datetime"
    )
    
    # Drop the datetime column as we already have a date column
    merged_df.drop(["datetime"],axis=1,inplace=True)
    
    # Return the joined data frames
    return(merged_df)

@op(
    ins={"merged_df": In(pd.DataFrame)},
    out=Out(bool)
)

def load(merged_df):
    try:
        # Create a connection to the PostgreSQL database
        engine = create_engine(
            postgres_connection_string,
            poolclass=NullPool
        )
        
        # Create a dictionary with column names as the key and the VARCHAR 
        # type as the value. This will be used to specify data types for the
        # created database. We will change some of these types later.
        database_datatypes = dict(
            zip(merged_df.columns,[VARCHAR]*len(merged_df.columns))
        )
        
        # Set date column to have the TIMESTAMP datatype
        database_datatypes["date"] = TIMESTAMP
        
        # Set columns with DOUBLE PRECISION datatype
        for column in ["origin.latitude","origin.longitude","origin.elevation",
                      "destination.latitude","destination.longitude",
                      "destination.elevation","pressure","rain","wind_speed"]:
            database_datatypes[column] = DECIMAL
        
        # Set columns with INT datatype
        for column in ["aircraft.numberofengines","wind_direction"]:
            database_datatypes[column] = INT
        
        # Set columns with TIME datatype
        for column in ["duration","departure.scheduled","departure.actual",
                       "arrival_scheduled","arrival.actual"]:
            database_datatypes[column] = TIME
            
        # Open the connection to the PostgreSQL server
        with engine.connect() as conn:
            
            # Store the data frame contents to the flight_weather 
            # table, using the dictionary of data types created
            # above and replacing any existing table
            rowcount = merged_df.to_sql(
                name="flight_weather",
                schema="public",
                dtype=database_datatypes,
                con=engine,
                index=False,
                if_exists="replace"
            )
            logger.info("{} records loaded".format(rowcount))
            
        # Close the connection to PostgreSQL and dispose of 
        # the connection engine
        engine.dispose(close=True)
        
        # Return the number of rows inserted
        return rowcount > 0
    
    # Trap and handle any relevant errors
    except exc.SQLAlchemyError as error:
        logger.error("Error: %s" % error)
        return False