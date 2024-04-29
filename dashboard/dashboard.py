import panel as pn
import pandas as pd
from sqlalchemy import create_engine
import os
import warnings
from sqlalchemy import create_engine, text, exc
import pandas.io.sql as sqlio
from bokeh.plotting import figure

# Configure Panel to run in a notebook if applicable
pn.extension(template='fast')

postgres_host = os.getenv("POSTGRES_HOST", "localhost")
warnings.filterwarnings("ignore", category=UserWarning)
postgres_connect = f"postgresql://dap:dap@{postgres_host}:5432/projectdb"


def create_scatter_plot(column, location, rain):
    try:
        query_string = f"""
        SELECT 
            date as date,
            "{column}" AS {column},
            "{location}" AS pedestrian_traffic
        FROM 
            weather_aqi_footfall
        where
        rain = {rain}
        """

        # Connect to the PostgreSQL database
        engine = create_engine(postgres_connect)
        # Run the query and return the results as a data frame
        with engine.connect() as connection:
            data_frame = sqlio.read_sql_query(text(query_string), connection)

        # Bokeh visualization tools
        TOOLS = "hover,crosshair,pan,wheel_zoom,zoom_in,zoom_out,box_zoom,reset,tap,save,box_select,poly_select,lasso_select"

        # Create a Bokeh figure
        p = figure(
            title=f"{column} vs Pedestrian Traffic at {location}",
            x_axis_label=f"{column}",
            y_axis_label="Pedestrian Traffic Count",
            tools=TOOLS,
        )

        # Create a scatter plot
        p.scatter(
            x=data_frame[column],
            y=data_frame["pedestrian_traffic"],
            size=10,  # Dot size
            line_color="navy",
            fill_alpha=0.6,
        )

        # Show the visualization
        return p

    except exc.SQLAlchemyError as db_error:
        print("Database error:", db_error)


parameters = [
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
]
locations = [
    "Aston Quay/Fitzgeralds",
    "Bachelors walk/Bachelors way",
    "Baggot st lower/Wilton tce inbound",
    "Baggot st upper/Mespil rd/Bank",
    "Capel st/Mary street",
    "College Green/Bank Of Ireland",
    "College Green/Church Lane",
    "College st/Westmoreland st",
    "D'olier st/Burgh Quay",
    "Dame Street/Londis",
    "Dawson Street",
    "Dawson Street old",
    "Dawson Street/Molesworth",
    "Grafton st/Monsoon",
    "Grafton Street / Nassau Street / Suffolk Street",
    "Grafton Street/CompuB",
    "Grand Canal st upp/Clanwilliam place",
    "Grand Canal st upp/Clanwilliam place/Google",
    "Henry Street/Coles Lane/Dunnes",
    "Liffey st/Halfpenny Bridge",
    "Liffey Street old",
    "Mary st/Jervis st",
    "Newcomen Bridge/Charleville mall inbound",
    "Newcomen Bridge/Charleville mall outbound",
    "North Wall Quay/Samuel Beckett bridge East",
    "North Wall Quay/Samuel Beckett bridge West",
    "O'Connell St/Parnell St/AIB",
    "O'Connell St/Pennys Pedestrian",
    "O'Connell st/Princes st North",
    "O'Connell Street Pennys - PYRO EVO Temporary Counter",
    "Phibsborough Rd/Enniskerry Road",
    "Phibsborough Rd/Munster St (Removed due to Overcounting)",
    "Richmond st south/Portabello Harbour inbound",
    "Richmond st south/Portabello Harbour outbound",
    "Talbot st/Guineys",
    "Talbot st/Murrays Pharmacy",
    "Westmoreland Street East/Fleet street",
    "Westmoreland Street West/Carrolls",
]

parameter_column = pn.widgets.Select(name="Parameter", options=list(parameters))
location_column = pn.widgets.Select(name="Location", options=list(locations))
rain = pn.widgets.Switch(name="Switch")
rain_text = pn.widgets.StaticText(value="Rain : ")


# Interactive plots
@pn.depends(parameter_column.param.value, location_column.param.value, rain.param.value)
def update_scatter(column, location, rain):
    return create_scatter_plot(column, location, int(rain))


# Layout
dashboard = pn.Column(
    pn.Row(parameter_column, location_column, rain_text, rain), pn.Row(update_scatter)
)

# Display the dashboard
dashboard.servable()
