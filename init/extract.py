import json
import pandas as pd
from cassandra.cluster import Cluster
from dagster import op, Out, In, get_dagster_logger
from datetime import date, datetime
from pymongo import MongoClient, errors

mongo_connection_string = "mongodb://dap:dap@mongodb_database"
logger = get_dagster_logger()

@op(
    out=Out(bool)
)

def extract_flights() -> bool:
    result = True
    try:
        # Connect to the MongoDB database
        client = MongoClient(mongo_connection_string)
        
        # Connect to the flights database
        flights_db = client["flights"]
        
        # Connect to the flights collection
        flights_collection = flights_db["flights"]
    
        # Open the file containing the data
        with open("flights.json","r") as fh:
        
            # Load the JSON data from the file
            data = json.load(fh)
            
        for flight in data["flights"]:
            # we only want flights from Dublin
            if flight["origin"]["id"] == "EIDW":
                try:
                    # Create a key for the MongoDB collection. This 
                    # ensures that we cannot have duplicate documents
                    key="{} {} {}".format(
                        flight["date"],
                        flight["departure"]["scheduled"],
                        flight["aircraft"]["callsign"]
                    )
                    flight["_id"] = key
                    
                    # Insert the flight data as a document in the flights 
                    # collection
                    flights_collection.insert_one(flight)
                    
                # Trap and handle duplicate key errors
                except errors.DuplicateKeyError as err:
                    logger.error("Error: %s" % err)
                    continue
            
    # Trap and handle other errors
    except Exception as err:
        logger.error("Error: %s" % err)
        result = False
    
    # Return a Boolean indicating success or failure
    return result

@op(
    out=Out(bool)
)

def extract_weather() -> bool:
    result = False
    try:
        # Load the weather data into a Pandas data frame
        weather_df = pd.read_csv(
            "hly532.csv",
            
            # Tell Pandas which columns should be 
            # interpreted as a date
            parse_dates=['date'],
            
            # Skip 23 rows as these contain metadata
            skiprows=23, 
            
            # Using only the specified columns
            usecols=[0,2,10,12,14],
            
            # Tell Pandas how to parse dates
            date_format="%d-%b-%Y %H:%M",
            
            # Load the file as a memory-map (much faster)
            memory_map=True,
            
            # Load the entire file in one go, rather than in chunks
            low_memory=False
        )
        
        # Set the column names for the data frame
        weather_df.columns = ["DateTime","Rain","Pressure","Wind Speed","Wind Direction"]
        
        # Connect to the Cassandra database
        cassandra = Cluster(["cassandra_database"])
        
        # Connect to the default keyspace
        cassandra_session = cassandra.connect()
        
        # Create the weather keyspace if it doesn't exist
        cassandra_session.execute(
            """
            CREATE KEYSPACE IF NOT EXISTS weather
            WITH REPLICATION = {'class':'SimpleStrategy', 'replication_factor':1};
            """
        )
        
        # Ensure all further operations take place 
        # against the weather keyspace
        cassandra_session.execute(
            """
            USE weather;
            """
        )

        # Create the weather table if it does not exist
        cassandra_session.execute(
            """
            CREATE TABLE IF NOT EXISTS weather(
                datetime timestamp,
                rain double,
                pressure double,
                wind_speed double,
                wind_direction int,
                PRIMARY KEY(datetime)
            )
            """
        )
        
        # Create a format string for inserting data
        insert_string = """INSERT INTO weather (datetime,rain,pressure,
                                                wind_speed,wind_direction) 
                        VALUES ('{}', {}, {}, {}, {});"""
                        
        # Iterate over each row in the data frame
        for index, row in weather_df.iterrows():
            
            # Convert the row values to a list
            row_values = row.values.flatten().tolist()
            
            # Insert the row
            cassandra_session.execute(insert_string.format(*row_values))
    
    # Trap and handle errors
    except Exception as err:
        logger.error("Error: %s" % err)
    
    # If the insert was successful then set the result flag to True
    else:
        result = True
    
    # Return the result flag
    return(result)

