from dagster import job
from extract import *
from transform_and_load import *
from visualisation import *

@job
def etl():
    # Visualise data from PostgreSQL 
    visualise(
        # Load the joined data into PostgreSQL
        load(
            # Join the flights and weather data
            join(
                # Transform the stored flights data
                transform_flights(
                    # Extract and store the flights data
                    extract_flights()
                ),
                # Transform the stored weather data
                transform_weather(
                    # Extract and store the weather data
                    extract_weather()
                )
            )
        )
    )