import panel as pn
import pandas as pd
import os
import warnings
from sqlalchemy import create_engine, text, exc
import pandas.io.sql as sqlio
from bokeh.plotting import figure
import datetime as dt
from bokeh.models import LinearAxis, Range1d
import folium
from folium.plugins import MarkerCluster

# Apply the CSS class to Panel components
pn.extension()

postgres_host = os.getenv("POSTGRES_HOST", "localhost")
warnings.filterwarnings("ignore", category=UserWarning)
postgres_connect = f"postgresql://dap:dap@{postgres_host}:5432/projectdb"

data = {
    "Counter Locations": [
        "Henry Street/Coles Lane/Dunnes",
        "O'Connell st/Princes st North",
        "Mary st/Jervis st",
        "Capel st/Mary street",
        "Aston Quay/Fitzgeralds",
        "Grafton Street/CompuB",
        "Talbot st/Guineys",
        "D'olier st/Burgh Quay",
        "Dame Street/Londis",
        "Talbot st/Murrays Pharmacy",
        "O'Connell St/Parnell St/AIB",
        "Grafton Street / Nassau Street / Suffolk Street",
        "College Green/Bank Of Ireland",
        "O'Connell St/Pennys Pedestrian",
        "Grafton st/Monsoon",
        "Westmoreland Street East/Fleet street",
        "Dawson Street/Molesworth Pedestrian",
        "Liffey st/Halfpenny Bridge",
        "Westmoreland Street West/Carrolls",
        "College Green/Church Lane",
        "College st/Westmoreland st",
        "Bachelors walk/Bachelors way",
        "Baggot st lower/Wilton tce inbound",
        "Baggot st upper/Mespil rd/Bank",
        "Grand Canal st upp/Clanwilliam place",
        "Grand Canal st upp/Clanwilliam place/Google",
        "Newcomen Bridge/Charleville mall inbound",
        "Newcomen Bridge/Charleville mall outbound",
        "North Wall Quay/Samuel Beckett bridge East",
        "North Wall Quay/Samuel Beckett bridge West",
        "Phibsborough Rd/Enniskerry Road",
        "Phibsborough Rd/Munster St (Removed due to Overcounting)",
        "Richmond st south/Portabello Harbour inbound",
        "Richmond st south/Portabello Harbour outbound",
    ],
    "Latitude": [
        53.34973,
        53.34902,
        53.34877,
        53.34842,
        53.34662,
        53.34337,
        53.35054,
        53.3469,
        53.34424,
        53.35012,
        53.352317,
        53.34352,
        53.34505,
        53.34874,
        53.34082,
        53.34554,
        53.341194,
        53.34687,
        53.346347,
        53.344263,
        53.345099,
        53.347199,
        53.33448,
        53.33385,
        53.33851,
        53.33851,
        53.35645,
        53.35648,
        53.346,
        53.34748,
        53.36334,
        53.36322,
        53.33034,
        53.33023,
    ],
    "Longitude": [
        -6.2609,
        -6.26005,
        -6.26674,
        -6.26918,
        -6.25982,
        -6.25898,
        -6.25528,
        -6.25872,
        -6.26116,
        -6.2577,
        -6.261675,
        -6.25912,
        -6.25939,
        -6.26011,
        -6.26035,
        -6.25919,
        -6.258337,
        -6.26335,
        -6.259197,
        -6.260774,
        -6.258778,
        -6.260863,
        -6.24577,
        -6.24469,
        -6.2379,
        -6.239,
        -6.24418,
        -6.24418,
        -6.24173,
        -6.24132,
        -6.27187,
        -6.27247,
        -6.26427,
        -6.26397,
    ],
}

# Convert data to DataFrame
df = pd.DataFrame(data)


# Function to create map HTML
def create_map():
    # Create a map centered around Dublin
    map_center = [53.349805, -6.26031]  # Dublin coordinates
    m = folium.Map(location=map_center, zoom_start=13)

    # Add marker cluster to improve performance for a large number of markers
    marker_cluster = MarkerCluster().add_to(m)

    # Add markers for each counter location
    for idx, row in df.iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            tooltip=row["Counter Locations"],
        ).add_to(marker_cluster)

    return m


def get_dataset():
    try:
        query_string = """
        SELECT 
            *
        FROM 
            weather_aqi_footfall
        limit 
            20
        """

        # Connect to the PostgreSQL database
        engine = create_engine(postgres_connect)
        # Run the query and return the results as a data frame
        data_frame = pd.DataFrame()
        with engine.connect() as connection:
            data_frame = sqlio.read_sql_query(text(query_string), connection)

        return data_frame

    except exc.SQLAlchemyError as db_error:
        print("Database error:", db_error)


def create_scatter_plot(column, location, daterange):
    (start_date, end_date) = daterange

    try:
        query_string = f"""
        SELECT 
            date as date,
            "{column}" AS {column},
            "{location}" AS pedestrian_traffic
        FROM 
            weather_aqi_footfall
            
        WHERE date >= '{start_date.strftime("%Y-%m-%d %H:%M:%S")}' 
        AND date <= '{end_date.strftime("%Y-%m-%d %H:%M:%S")}'

        """

        # Connect to the PostgreSQL database
        engine = create_engine(postgres_connect)
        # Run the query and return the results as a data frame
        with engine.connect() as connection:
            data_frame = sqlio.read_sql_query(text(query_string), connection)

        # Bokeh visualization tools
        tools = "crosshair,pan,wheel_zoom,zoom_in,zoom_out,reset,save,"

        # Create a Bokeh figure
        p = figure(
            title=f"{column} vs Pedestrian Traffic at {location}",
            x_axis_label=f"{column}",
            y_axis_label="Pedestrian Traffic Count",
            tools=tools,
            min_width=800,
        )

        # Create a scatter plot
        p.scatter(
            x=data_frame[column],
            y=data_frame["pedestrian_traffic"],
            size=5,  # Dot size
            line_color="navy",
            fill_alpha=0.6,
        )

        # Show the visualization
        return p

    except exc.SQLAlchemyError as db_error:
        print("Database error:", db_error)


def create_line_plot(var, loc, daterange, avgby):
    match avgby:
        case "Daily":
            avgd = "D"
        case "Monthly":
            avgd = "ME"
        case "Weekly":
            avgd = "W"
        case _:
            avgd = "D"

    try:
        (start_date, end_date) = daterange
        query_string = f"""
            SELECT date, {var}, "{loc}"
            FROM weather_aqi_footfall
            WHERE date >= '{start_date.strftime("%Y-%m-%d %H:%M:%S")}' 
            AND date <= '{end_date.strftime("%Y-%m-%d %H:%M:%S")}'
            """
        engine = create_engine(postgres_connect)
        with engine.connect() as connection:
            data_frame = sqlio.read_sql_query(text(query_string), connection)
        data_frame["date"] = pd.to_datetime(data_frame["date"])
        data_frame.set_index("date", inplace=True)
        monthly_avg_data = data_frame.resample(avgd).mean()

        tools = "crosshair,pan,wheel_zoom,zoom_in,zoom_out,reset,save,"

        # Bokeh plot setup
        p = figure(
            x_axis_type="datetime",
            title=f"Distribution of {var} and footfall at {loc}",
            min_width=800,
            tools=tools,
        )
        p.xaxis.axis_label = "Date"
        p.yaxis.axis_label = "Pedestrian count"
        # Second y-axis with different scale
        p.extra_y_ranges = {
            "y1": Range1d(start=0, end=monthly_avg_data[loc].max() * 1.1),
            "y2": Range1d(start=0, end=monthly_avg_data[var].max() * 1.1),
        }
        # p.add_layout(LinearAxis(y_range_name="y1", axis_label=f"{loc}"), "left")
        p.add_layout(LinearAxis(y_range_name="y2", axis_label=f"{var}"), "right")

        p.line(
            monthly_avg_data.index,
            monthly_avg_data[var],
            line_color="blue",
            y_range_name="y2",
            legend_label=var,
        )
        p.line(
            monthly_avg_data.index,
            monthly_avg_data[loc],
            line_color="green",
            y_range_name="y1",
            legend_label="Pedestrian count",
        )

        p.legend.location = "top_left"
        p.legend.click_policy = "hide"

        return p  # Show the plot

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
    "Grafton st/Monsoon",
    "Grafton Street / Nassau Street / Suffolk Street",
    "Grafton Street/CompuB",
    "Grand Canal st upp/Clanwilliam place",
    "Grand Canal st upp/Clanwilliam place/Google",
    "Henry Street/Coles Lane/Dunnes",
    "Mary st/Jervis st",
    "Newcomen Bridge/Charleville mall inbound",
    "Newcomen Bridge/Charleville mall outbound",
    "North Wall Quay/Samuel Beckett bridge East",
    "North Wall Quay/Samuel Beckett bridge West",
    "O'Connell St/Parnell St/AIB",
    "O'Connell St/Pennys Pedestrian",
    "O'Connell st/Princes st North",
    "Phibsborough Rd/Enniskerry Road",
    "Richmond st south/Portabello Harbour inbound",
    "Richmond st south/Portabello Harbour outbound",
    "Talbot st/Guineys",
    "Westmoreland Street East/Fleet street",
    "Westmoreland Street West/Carrolls",
]


#############################
button_4 = pn.widgets.Button(
    name="Project Report",
    button_type="primary",
    styles={"width": "100%"},
)
button_3 = pn.widgets.Button(
    name="Distribution of variables",
    button_type="primary",
    styles={"width": "100%"},
)
button_1 = pn.widgets.Button(
    name="Relationship b/w variables",
    button_type="primary",
    styles={"width": "100%"},
)
button_2 = pn.widgets.Button(
    name="Dataset",
    button_type="primary",
    styles={"width": "100%"},
)
button_0 = pn.widgets.Button(
    name="Introduction",
    button_type="primary",
    styles={"width": "100%"},
)


button_0.on_click(lambda event: show_page("page_0"))
button_1.on_click(lambda event: show_page("page_1"))
button_2.on_click(lambda event: show_page("page_2"))
button_3.on_click(lambda event: show_page("page_3"))
button_4.on_click(lambda event: show_page("page_4"))


def createpage_0():
    # Create Panel app
    map_viewer = pn.pane.plot.Folium(create_map(), height=400)

    page = pn.Column(
        pn.Row(pn.pane.Markdown("# Introduction")),
        pn.Row(
            pn.pane.Markdown("""
                                ### Enviornmental variables
                                - **_id**: Unique identifier for each data entry.
                                - **date**: Date and time of the recorded data.
                                - **temperature_2m**: Temperature at 2 meters above ground level in Celsius.
                                - **relative_humidity_2m**: Relative humidity at 2 meters above ground level, expressed as a percentage.
                                - **dew_point_2m**: Dew point temperature at 2 meters above ground level in Celsius.
                                - **apparent_temperature**: Perceived temperature, taking into account factors like humidity and wind, in Celsius.
                                - **precipitation**: Total precipitation in millimeters.
                                - **rain**: Amount of rainfall in millimeters.
                                - **snowfall**: Amount of snowfall in millimeters.
                                - **weather_code**: Numerical code representing the weather conditions.
                                - **cloud_cover**: Percentage of sky covered by clouds.
                                - **wind_speed_10m**: Wind speed at 10 meters above ground level in meters per second.
                                - **wind_direction_10m**: Wind direction at 10 meters above ground level in degrees.
                                - **is_day**: Binary indicator (0 or 1) indicating whether it's daytime.
                                - **sunshine_duration**: Duration of sunshine in minutes.
                                - **pm10**: Particulate Matter (PM10) concentration in micrograms per cubic meter.
                                - **pm2_5**: Particulate Matter (PM2.5) concentration in micrograms per cubic meter.
                                - **carbon_monoxide**: Carbon Monoxide (CO) concentration in micrograms per cubic meter.
                                - **nitrogen_dioxide**: Nitrogen Dioxide (NO2) concentration in micrograms per cubic meter.
                                - **sulphur_dioxide**: Sulphur Dioxide (SO2) concentration in micrograms per cubic meter.
                                - **dust**: Dust concentration in micrograms per cubic meter.
                                - **european_aqi**: European Air Quality Index (AQI) calculated based on various pollutant concentrations.
                                - **european_aqi_pm2_5**: European AQI specifically calculated for PM2.5.
                                - **european_aqi_pm10**: European AQI specifically calculated for PM10.
                                - **european_aqi_nitrogen_dioxide**: European AQI specifically calculated for nitrogen dioxide (NO2).
                                - **european_aqi_ozone**: European AQI specifically calculated for ozone (O3).
                                - **european_aqi_sulphur_dioxide**: European AQI specifically calculated for sulphur dioxide (SO2).
                                """),
            pn.pane.Markdown("""
                                 ### Counter Locations
                                - Aston Quay/Fitzgeralds
                                - Bachelors walk/Bachelors way
                                - Baggot st lower/Wilton tce inbound
                                - Baggot st upper/Mespil rd/Bank
                                - Capel st/Mary street
                                - College Green/Bank Of Ireland
                                - College Green/Church Lane
                                - College st/Westmoreland st
                                - D'olier st/Burgh Quay
                                - Dame Street/Londis
                                - Grafton st/Monsoon
                                - Grafton Street / Nassau Street / Suffolk Street
                                - Grafton Street/CompuB
                                - Grand Canal st upp/Clanwilliam place
                                - Grand Canal st upp/Clanwilliam place/Google
                                - Henry Street/Coles Lane/Dunnes
                                - Mary st/Jervis st
                                - Newcomen Bridge/Charleville mall inbound
                                - Newcomen Bridge/Charleville mall outbound
                                - North Wall Quay/Samuel Beckett bridge East
                                - North Wall Quay/Samuel Beckett bridge West
                                - O'Connell St/Parnell St/AIB
                                - O'Connell St/Pennys Pedestrian
                                - O'Connell st/Princes st North
                                - Phibsborough Rd/Enniskerry Road
                                - Richmond st south/Portabello Harbour inbound
                                - Richmond st south/Portabello Harbour outbound
                                - Talbot st/Guineys
                                - Westmoreland Street East/Fleet street
                                - Westmoreland Street West/Carrolls
                                 
                                 """),
        ),
        pn.Row(map_viewer),
    )

    return page


def createpage_1():
    parameter_column = pn.widgets.Select(name="Parameter", options=list(parameters))
    location_column = pn.widgets.Select(name="Location", options=list(locations))
    date_range_slider = pn.widgets.DateRangeSlider(
        name="Date Range",
        start=dt.datetime(2023, 1, 1, 00, 00),
        end=dt.datetime(2023, 12, 31, 23, 59),
        value=(dt.datetime(2023, 1, 1, 00, 00), dt.datetime(2023, 12, 31, 23, 59)),
        step=1,
    )

    # Interactive plots
    @pn.depends(
        parameter_column.param.value,
        location_column.param.value,
        date_range_slider.param.value,
    )
    def update_scatter(column, location, daterange):
        return create_scatter_plot(column, location, daterange)

    # Layout
    page = pn.FlexBox(
        pn.Column(update_scatter),
        pn.Column(
            parameter_column,
            location_column,
            date_range_slider,
            width=300,
        ),
        flex_direction="row",
        flex_wrap="nowrap",
        justify_content="space-evenly",
        align_content="stretch",
        sizing_mode="stretch_width",
    )

    return page


def createpage_2():
    df = get_dataset()
    page = pn.Column(
        pn.Row(
            pn.pane.Markdown("""## Dataset Explorer
                         (First 20 rows of the data)
                         """),
        ),
        pn.Column(pn.pane.DataFrame(df), height=500),
        align="center",
    )
    return page


def createpage_3():
    parameter_column = pn.widgets.Select(name="Parameter", options=list(parameters))
    location_column = pn.widgets.Select(name="Location", options=list(locations))
    date_range_slider = pn.widgets.DateRangeSlider(
        name="Date Range",
        start=dt.datetime(2023, 1, 1, 00, 00),
        end=dt.datetime(2023, 12, 31, 23, 59),
        value=(dt.datetime(2023, 1, 1, 00, 00), dt.datetime(2023, 12, 31, 23, 59)),
        step=1,
    )
    toggle_group = pn.widgets.ToggleGroup(
        name="Averageby",
        options=["Daily", "Weekly", "Monthly"],
        behavior="radio",
        button_type="light",
    )

    # Interactive plots
    @pn.depends(
        parameter_column.param.value,
        location_column.param.value,
        date_range_slider.param.value,
        toggle_group.param.value,
    )
    def update_line(column, location, daterange, avgby):
        return create_line_plot(
            column,
            location,
            daterange,
            avgby,
        )

    # Layout
    page = pn.FlexBox(
        pn.Column(update_line),
        pn.Column(
            parameter_column,
            location_column,
            date_range_slider,
            pn.pane.HTML("Average by:"),
            toggle_group,
            width=300,
        ),
        flex_direction="row",
        flex_wrap="nowrap",
        justify_content="space-evenly",
        align_content="stretch",
        sizing_mode="stretch_width",
    )

    return page


def createpage_4():
    pdf_pane = pn.pane.PDF("dashboard\conference.pdf", width=1100, height=600)
    return pdf_pane


mapping = {
    "page_0": createpage_0(),
    "page_1": createpage_1(),
    "page_2": createpage_2(),
    "page_3": createpage_3(),
    "page_4": createpage_4(),
}

main_area = pn.Column(mapping["page_0"], width=1100)
sidebar = pn.Column(
    button_0,
    button_2,
    button_1,
    button_3,
    button_4,
    pn.layout.Divider(margin=(220, 0, 0, 0)),
    pn.pane.Markdown("""
                     **© DAP PROJECT JAN 2024 TEAM AA**

                        - Ankith Babu Joseph- x23185813
                        - Alphons Zacharia James- x23169702
                        - Abhilash Janardhanan- x23121424
                     """),
    styles={"width": "100%", "padding": "15px"},
)


def show_page(page_key):
    main_area.clear()
    main_area.append(mapping[page_key])


dashboard = pn.template.MaterialTemplate(
    title="Dashboard - Exploring the impact of environmental factors on pedestrian footfall in Dublin city",
    sidebar=[sidebar],
    main=[main_area],
    sidebar_width=300,
)

# Serve the Panel app
dashboard.servable()
