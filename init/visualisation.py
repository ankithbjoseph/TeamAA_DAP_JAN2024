import pandas.io.sql as sqlio
import psycopg2
from dagster import op, In
from bokeh.plotting import figure, show
from sqlalchemy import create_engine, event, text, exc
from sqlalchemy.engine.url import URL

@op(
    ins={"start": In(bool)}
)

def visualise(start):
    
    postgres_connection_string = "postgresql://dap:dap@postgres_database:5432/flights"

    # A query to return the number of minutes delay in departures and the rainfall
    query_string = """
    SELECT 
        EXTRACT(HOURS FROM "departure.actual" - "departure.scheduled")*60 + 
        EXTRACT(MINUTES FROM "departure.actual" - "departure.scheduled") AS delay,
        rain
    FROM 
        flight_weather;
    """

    try:
        # Connect to the PostgreSQL database
        engine = create_engine(postgres_connection_string)     
        # Run the query and return the results as a data frame
        with engine.connect() as connection:
            flights_dataframe = sqlio.read_sql_query(
                text(query_string), 
                connection
            )
        TOOLS = """hover,crosshair,pan,wheel_zoom,zoom_in,zoom_out,
            box_zoom,reset,tap,save,box_select,poly_select,
            lasso_select"""

        # Create a Bokeh figure
        p = figure(
            title="Flight Delay vs Rainfall",
            x_axis_label="Rainfall in mm",
            y_axis_label="Flight delay in minutes",
            tools = TOOLS
        )
        # Create a scatter plot
        p.scatter(
            # the x variable
            flights_dataframe["rain"],
            # the y variable
            flights_dataframe["delay"]
        )
        # show the visualisation
        show(p)
       # return p
    except exc.SQLAlchemyError as dbError:
        print ("PostgreSQL Error", dbError)
    finally:
        if engine in locals(): 
            engine.close()