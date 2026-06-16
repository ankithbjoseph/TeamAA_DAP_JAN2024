import panel as pn
import pandas as pd
import os
import warnings
import logging
from sqlalchemy import create_engine, text, exc
import pandas.io.sql as sqlio
from bokeh.plotting import figure
from bokeh.models import LinearAxis, Range1d, HoverTool
import datetime as dt
import folium
from folium.plugins import MarkerCluster

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning)

# ── Environment ───────────────────────────────────────────────────────────────
postgres_host     = os.getenv("POSTGRES_HOST", "localhost")
postgres_user     = os.getenv("POSTGRES_USER", "")
postgres_password = os.getenv("POSTGRES_PASSWORD", "")
postgres_port     = os.getenv("POSTGRES_PORT", "5432")
postgres_db       = os.getenv("POSTGRES_DB_APP", "projectdb")
postgres_connect  = (
    f"postgresql://{postgres_user}:{postgres_password}"
    f"@{postgres_host}:{postgres_port}/{postgres_db}"
)

# Single engine instance reused across all requests
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(postgres_connect)
    return _engine


# ── Static data ───────────────────────────────────────────────────────────────
df_locations = pd.read_csv("filtered_locations.csv")

parameters_dict = {
    "temperature_2m":                "°C",
    "relative_humidity_2m":          "%",
    "dew_point_2m":                  "°C",
    "apparent_temperature":          "°C",
    "precipitation":                 "mm",
    "rain":                          "mm",
    "snowfall":                      "cm",
    "cloud_cover":                   "%",
    "wind_speed_10m":                "km/h",
    "sunshine_duration":             "Seconds",
    "pm10":                          "μg/m³",
    "pm2_5":                         "μg/m³",
    "carbon_monoxide":               "μg/m³",
    "nitrogen_dioxide":              "μg/m³",
    "sulphur_dioxide":               "μg/m³",
    "dust":                          "μg/m³",
    "european_aqi":                  "",
    "european_aqi_pm2_5":            "",
    "european_aqi_pm10":             "",
    "european_aqi_nitrogen_dioxide": "",
    "european_aqi_ozone":            "",
    "european_aqi_sulphur_dioxide":  "",
}

VALID_COLUMNS = set(parameters_dict.keys())

locations = [
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

VALID_LOCATIONS = set(locations)

# ── Design tokens ─────────────────────────────────────────────────────────────
C_PRIMARY    = "#1E40AF"
C_ACCENT     = "#D97706"
C_BG         = "#FFFFFF"
C_PAGE_BG    = "#F8FAFC"
C_GRID       = "#E9EEF6"
C_TEXT       = "#1E3A8A"
C_TEXT_MUTED = "#64748B"
C_BORDER     = "#DBEAFE"

_CARD_STYLE = {
    "background":    "#FFFFFF",
    "border":        "1px solid #DBEAFE",
    "border-radius": "8px",
    "box-shadow":    "0 1px 4px rgba(30,64,175,.10)",
    "padding":       "20px 24px",
    "margin-bottom": "16px",
}

_H2_CSS = (
    "font-family:'Fira Code',monospace;font-size:22px;font-weight:600;"
    "color:#1E3A8A;margin:0 0 6px;letter-spacing:-0.01em;"
)
_LEAD_CSS = (
    "font-family:'Fira Sans',sans-serif;font-size:13px;"
    "color:#64748B;margin:0;line-height:1.6;"
)
_CODE_CSS = (
    "background:#E9EEF6;padding:1px 6px;border-radius:4px;"
    "font-family:'Fira Code',monospace;font-size:12px;"
)
_SUB_H_CSS = (
    "font-family:'Fira Sans',sans-serif;font-size:11px;font-weight:700;"
    "color:#1E40AF;margin:0 0 8px;letter-spacing:0.04em;text-transform:uppercase;"
)


def _page_header(title: str, subtitle: str = "") -> pn.pane.HTML:
    sub = f'<p style="{_LEAD_CSS}">{subtitle}</p>' if subtitle else ""
    return pn.pane.HTML(
        f'<div style="padding:0 0 20px;border-bottom:1px solid #DBEAFE;margin-bottom:8px;">'
        f'  <h2 style="{_H2_CSS}">{title}</h2>'
        f'  {sub}'
        f'</div>',
        sizing_mode="stretch_width",
    )


# ── Chart helpers ─────────────────────────────────────────────────────────────
def _style_figure(p):
    p.background_fill_color = C_BG
    p.border_fill_color     = C_PAGE_BG
    p.outline_line_color    = C_BORDER
    p.sizing_mode           = "stretch_width"
    for ax in list(p.xaxis) + list(p.yaxis):
        ax.axis_line_color        = C_BORDER
        ax.major_tick_line_color  = C_BORDER
        ax.minor_tick_line_color  = None
        ax.axis_label_text_color  = C_TEXT
        ax.major_label_text_color = C_TEXT_MUTED
    for gr in list(p.xgrid) + list(p.ygrid):
        gr.grid_line_color = C_GRID
        gr.grid_line_alpha = 0.8
    p.title.text_color      = C_TEXT
    p.title.text_font_size  = "14px"
    p.title.text_font_style = "normal"
    return p


def _style_legend(p):
    p.legend.border_line_color     = C_BORDER
    p.legend.background_fill_color = C_BG
    p.legend.background_fill_alpha = 0.92
    p.legend.label_text_color      = C_TEXT
    p.legend.label_text_font_size  = "12px"
    p.legend.click_policy          = "hide"


def _chart_col(*items) -> pn.Column:
    return pn.Column(
        *items,
        styles={
            "background":    "#FFFFFF",
            "border":        "1px solid #DBEAFE",
            "border-radius": "8px",
            "box-shadow":    "0 1px 4px rgba(30,64,175,.10)",
            "padding":       "16px",
            "flex":          "1 1 320px",
            "min-width":     "0",
            "overflow":      "hidden",
        },
        sizing_mode="stretch_width",
    )


def _controls_col(*widgets) -> pn.Column:
    return pn.Column(
        *widgets,
        styles={
            "background":    "#FFFFFF",
            "border":        "1px solid #DBEAFE",
            "border-radius": "8px",
            "box-shadow":    "0 1px 4px rgba(30,64,175,.10)",
            "padding":       "16px 18px",
            "flex":          "0 0 260px",
            "min-width":     "200px",
        },
        css_classes=["dap-controls"],
    )


# ── Data functions ────────────────────────────────────────────────────────────
def create_map() -> folium.Map:
    m = folium.Map(location=[53.349805, -6.26031], zoom_start=13)
    cluster = MarkerCluster().add_to(m)
    for _, row in df_locations.iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            tooltip=row["Counter Locations"],
        ).add_to(cluster)
    return m


def get_dataset() -> pd.DataFrame:
    try:
        q = text("SELECT * FROM weather_aqi_footfall LIMIT 20")
        with get_engine().connect() as conn:
            return sqlio.read_sql_query(q, conn)
    except exc.SQLAlchemyError as e:
        log.error("DB error in get_dataset: %s", e)
        return pd.DataFrame()


def create_scatter_plot(column: str, location: str, daterange):
    # Whitelist validation prevents SQL injection via column/location names
    if column not in VALID_COLUMNS or location not in VALID_LOCATIONS:
        return pn.pane.Alert("Invalid parameter selection.", alert_type="danger")
    start_date, end_date = daterange
    try:
        q = text(f"""
            SELECT date, "{column}", "{location}" AS pedestrian_traffic
            FROM weather_aqi_footfall
            WHERE date BETWEEN :start AND :end
        """)
        with get_engine().connect() as conn:
            df = sqlio.read_sql_query(
                q, conn,
                params={
                    "start": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "end":   end_date.strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
        unit  = parameters_dict[column]
        label = f"{column} ({unit})" if unit else column
        p = figure(
            title=f"{column}  ↔  Pedestrian traffic · {location}",
            x_axis_label=label,
            y_axis_label="Pedestrian Count",
            tools="crosshair,pan,wheel_zoom,zoom_in,zoom_out,reset,save",
            height=420,
        )
        _style_figure(p)
        p.add_tools(HoverTool(tooltips=[
            (column,             f"@{{{column}}}"),
            ("Pedestrian count", "@pedestrian_traffic"),
        ]))
        p.scatter(
            x=df[column],
            y=df["pedestrian_traffic"],
            size=5,
            color=C_PRIMARY,
            alpha=0.55,
            line_color=None,
        )
        return p
    except exc.SQLAlchemyError as e:
        log.error("DB error in create_scatter_plot: %s", e)
        return pn.pane.Alert("Failed to load chart data.", alert_type="danger")


def create_line_plot(var: str, loc: str, daterange, avgby: str):
    if var not in VALID_COLUMNS or loc not in VALID_LOCATIONS:
        return pn.pane.Alert("Invalid parameter selection.", alert_type="danger")
    freq = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}.get(avgby, "D")
    start_date, end_date = daterange
    try:
        q = text(f"""
            SELECT date, "{var}", "{loc}"
            FROM weather_aqi_footfall
            WHERE date BETWEEN :start AND :end
        """)
        with get_engine().connect() as conn:
            df = sqlio.read_sql_query(
                q, conn,
                params={
                    "start": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "end":   end_date.strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        avg = df.resample(freq).mean()

        unit  = parameters_dict[var]
        label = f"{var} ({unit})" if unit else var

        p = figure(
            x_axis_type="datetime",
            title=f"{var}  &  footfall at {loc}  ·  {avgby} average",
            tools="crosshair,pan,wheel_zoom,zoom_in,zoom_out,reset,save",
            height=420,
        )
        _style_figure(p)
        p.xaxis.axis_label = "Date"
        p.y_range          = Range1d(start=0, end=avg[var].max() * 1.1)
        p.yaxis.axis_label = label

        p.extra_y_ranges = {"y2": Range1d(start=0, end=avg[loc].max() * 1.1)}
        p.add_layout(
            LinearAxis(
                y_range_name="y2",
                axis_label="Pedestrian Count",
                axis_line_color=C_BORDER,
                major_tick_line_color=C_BORDER,
                minor_tick_line_color=None,
                axis_label_text_color=C_TEXT,
                major_label_text_color=C_TEXT_MUTED,
            ),
            "right",
        )

        p.line(avg.index, avg[var], line_color=C_PRIMARY, line_width=2,
               legend_label=var)
        p.line(avg.index, avg[loc], line_color=C_ACCENT,  line_width=2,
               y_range_name="y2", legend_label="Pedestrian count",
               line_dash="dashed")

        p.legend.location = "top_left"
        _style_legend(p)
        return p
    except exc.SQLAlchemyError as e:
        log.error("DB error in create_line_plot: %s", e)
        return pn.pane.Alert("Failed to load chart data.", alert_type="danger")


# ── Custom CSS ────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');

:root {
  --c-primary:  #1E40AF;
  --c-accent:   #D97706;
  --c-bg:       #F8FAFC;
  --c-surface:  #FFFFFF;
  --c-muted:    #E9EEF6;
  --c-border:   #DBEAFE;
  --c-text:     #1E3A8A;
  --c-muted-t:  #64748B;
  --radius:     8px;
  --shadow:     0 1px 4px rgba(30,64,175,.10);
  --t:          150ms ease-out;

  /* Spacing scale */
  --sp-1: 4px;  --sp-2: 8px;   --sp-3: 12px;  --sp-4: 16px;
  --sp-5: 20px; --sp-6: 24px;  --sp-8: 32px;  --sp-10: 40px;
}

body, .bk-root {
  font-family: 'Fira Sans', system-ui, sans-serif !important;
  background: var(--c-bg) !important;
}

/* ── App bar ─────────────────────────────────────────────────── */
.mdc-top-app-bar {
  background: var(--c-primary) !important;
  box-shadow: 0 2px 8px rgba(30,64,175,.30) !important;
}
.mdc-top-app-bar__title {
  font-family: 'Fira Code', monospace !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  letter-spacing: .03em !important;
}

/* ── Sidebar background ──────────────────────────────────────── */
.mdc-drawer, .mdc-drawer__content {
  background: linear-gradient(175deg, #1E3A8A 0%, #1E40AF 100%) !important;
  border-right: none !important;
}

/* ── Sidebar nav (RadioButtonGroup vertical) ─────────────────── */
.mdc-drawer .bk-btn-group {
  display: flex !important;
  flex-direction: column !important;
  gap: 2px !important;
  padding: 4px 8px !important;
}
.mdc-drawer .bk-btn-group .bk-btn {
  text-align: left !important;
  border: none !important;
  border-left: 3px solid transparent !important;
  border-radius: 6px !important;
  background: transparent !important;
  color: rgba(255,255,255,.78) !important;
  font-family: 'Fira Sans', sans-serif !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  padding: 10px 14px !important;
  cursor: pointer !important;
  transition: background var(--t), color var(--t) !important;
  width: 100% !important;
}
.mdc-drawer .bk-btn-group .bk-btn:hover {
  background: rgba(255,255,255,.12) !important;
  color: #fff !important;
}
.mdc-drawer .bk-btn-group .bk-btn.bk-active {
  background: rgba(255,255,255,.18) !important;
  color: #fff !important;
  font-weight: 600 !important;
  border-left-color: #D97706 !important;
}

/* ── Main content area ───────────────────────────────────────── */
.mdc-drawer-app-content { background: var(--c-bg) !important; }

/* ── Widgets (Select, DateRange) ─────────────────────────────── */
.bk-input, select.bk-input {
  border: 1px solid var(--c-border) !important;
  border-radius: 6px !important;
  font-family: 'Fira Sans', sans-serif !important;
  font-size: 13px !important;
  color: var(--c-text) !important;
  background: #fff !important;
  padding: 6px 10px !important;
  transition: border-color var(--t), box-shadow var(--t) !important;
  width: 100% !important;
}
.bk-input:focus, select.bk-input:focus {
  border-color: #3B82F6 !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,.20) !important;
  outline: none !important;
}
.bk-slider-title, .bk-input-group label {
  font-family: 'Fira Sans', sans-serif !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  color: var(--c-text) !important;
  letter-spacing: .03em !important;
}

/* ── ToggleGroup (avg-by buttons) ────────────────────────────── */
.dap-controls .bk-btn-group {
  display: flex !important;
  flex-direction: row !important;
  gap: 4px !important;
  flex-wrap: nowrap !important;
  align-items: stretch !important;
  width: 100% !important;
}
.dap-controls .bk-btn-group .bk-btn {
  border: 1px solid var(--c-border) !important;
  border-radius: 6px !important;
  background: #fff !important;
  color: var(--c-muted-t) !important;
  font-family: 'Fira Sans', sans-serif !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  padding: 0 8px !important;
  min-height: 36px !important;
  flex: 1 1 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  cursor: pointer !important;
  transition: background var(--t), color var(--t), border-color var(--t) !important;
  white-space: nowrap !important;
}
.dap-controls .bk-btn-group .bk-btn:hover,
.dap-controls .bk-btn-group .bk-btn.bk-active {
  background: var(--c-primary) !important;
  border-color: var(--c-primary) !important;
  color: #fff !important;
}

/* ── Data table ──────────────────────────────────────────────── */
.dap-table-wrap {
  overflow-x: auto !important;
  -webkit-overflow-scrolling: touch !important;
  border-radius: var(--radius) !important;
  border: 1px solid var(--c-border) !important;
  background: var(--c-surface) !important;
  box-shadow: var(--shadow) !important;
}
.dataframe {
  width: 100% !important;
  border-collapse: collapse !important;
  font-family: 'Fira Sans', sans-serif !important;
  font-size: 12px !important;
}
.dataframe thead th {
  background: var(--c-muted) !important;
  color: var(--c-text) !important;
  font-family: 'Fira Code', monospace !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: .05em !important;
  padding: 9px 14px !important;
  text-align: left !important;
  border-bottom: 2px solid var(--c-border) !important;
  white-space: nowrap !important;
}
.dataframe tbody td {
  padding: 7px 14px !important;
  border-bottom: 1px solid var(--c-border) !important;
  color: var(--c-text) !important;
  font-family: 'Fira Code', monospace !important;
  white-space: nowrap !important;
}
.dataframe tbody tr:nth-child(even) td { background: var(--c-bg) !important; }
.dataframe tbody tr:hover td           { background: var(--c-muted) !important; }

/* ── Responsive ──────────────────────────────────────────────── */
@media (max-width: 768px) {
  /* Controls stack full-width below chart */
  .dap-controls {
    flex: 1 1 100% !important;
    max-width: 100% !important;
    min-width: unset !important;
  }

  /* Reduce page padding on mobile */
  .dap-page {
    padding: 16px !important;
  }

  /* Prevent iOS input zoom (needs 16px) */
  .bk-input, select.bk-input {
    font-size: 16px !important;
    min-height: 44px !important;
  }

  /* Larger touch targets for toggle buttons */
  .dap-controls .bk-btn-group .bk-btn {
    min-height: 44px !important;
    font-size: 13px !important;
  }

  /* Larger nav buttons */
  .mdc-drawer .bk-btn-group .bk-btn {
    font-size: 13px !important;
    min-height: 44px !important;
    padding: 12px 14px !important;
  }

  /* Shrink top bar title */
  .mdc-top-app-bar__title {
    font-size: 12px !important;
    letter-spacing: 0 !important;
  }

  /* Reduce intro card gap on mobile */
  .dap-intro-cards {
    gap: 12px !important;
  }
}
@media (max-width: 480px) {
  .mdc-top-app-bar__title { display: none !important; }

  /* Even tighter padding on small phones */
  .dap-page {
    padding: 12px !important;
  }
}
"""

pn.extension(raw_css=[CUSTOM_CSS])


# ── Sidebar ───────────────────────────────────────────────────────────────────
nav = pn.widgets.RadioButtonGroup(
    name="",
    options=["Introduction", "Dataset", "Relationship b/w variables",
             "Distribution of variables", "Project Report"],
    value="Introduction",
    orientation="vertical",
    button_type="default",
    sizing_mode="stretch_width",
)

sidebar = pn.Column(
    pn.pane.HTML(
        '<div style="padding:20px 16px 6px;font-family:\'Fira Code\',monospace;'
        'font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;'
        'color:rgba(255,255,255,.40);">Navigation</div>',
        sizing_mode="stretch_width",
    ),
    nav,
    pn.layout.Divider(
        margin=(12, 8, 4, 8),
        stylesheets=["hr { border-color: rgba(255,255,255,.15) !important; }"],
    ),
    pn.pane.HTML(
        '<div style="padding:12px;margin:0 8px 8px;border-radius:8px;'
        'background:rgba(255,255,255,.08);font-family:\'Fira Sans\',sans-serif;'
        'font-size:11px;color:rgba(255,255,255,.55);line-height:1.9;">'
        '<div style="font-size:10px;font-weight:700;letter-spacing:.1em;'
        'text-transform:uppercase;color:rgba(255,255,255,.30);margin-bottom:8px;">'
        'DAP Project · Jan 2024</div>'
        'Ankith Babu Joseph · x23185813<br>'
        'Alphons Zacharia James · x23169702<br>'
        'Abhilash Janardhanan · x23121424'
        '</div>',
        sizing_mode="stretch_width",
    ),
    styles={"width": "100%", "padding": "0"},
)


# ── Pages ─────────────────────────────────────────────────────────────────────
def createpage_0():
    map_viewer = pn.pane.plot.Folium(create_map(), height=420, sizing_mode="stretch_width")

    env_html = (
        '<ul style="list-style:none;padding:0;margin:0;font-family:\'Fira Sans\',sans-serif;'
        'font-size:13px;color:#1E3A8A;line-height:2.1;">'
        + "".join(
            f'<li><code style="background:#E9EEF6;padding:1px 6px;border-radius:4px;'
            f'font-family:\'Fira Code\',monospace;font-size:11px;">{k}</code>'
            f'&nbsp;<span style="color:#64748B;">({v})</span></li>'
            for k, v in list(parameters_dict.items())[:10]
        )
        + '</ul>'
    )

    aqi_html = (
        '<ul style="list-style:none;padding:0;margin:0;font-family:\'Fira Sans\',sans-serif;'
        'font-size:13px;color:#1E3A8A;line-height:2.1;">'
        + "".join(
            f'<li><code style="background:#E9EEF6;padding:1px 6px;border-radius:4px;'
            f'font-family:\'Fira Code\',monospace;font-size:11px;">{k}</code>'
            + (f'&nbsp;<span style="color:#64748B;">({v})</span>' if v else "")
            + '</li>'
            for k, v in list(parameters_dict.items())[10:]
        )
        + '</ul>'
    )

    loc_html = (
        '<ul style="list-style:none;padding:0;margin:0;font-family:\'Fira Sans\',sans-serif;'
        'font-size:12px;color:#1E3A8A;line-height:2;">'
        + "".join(f"<li>{loc}</li>" for loc in locations)
        + '</ul>'
    )

    def _info_card(badge: str, title: str, body_html: str) -> pn.Column:
        return pn.Column(
            pn.pane.HTML(
                f'<span style="font-family:\'Fira Code\',monospace;font-size:10px;font-weight:700;'
                f'letter-spacing:.1em;text-transform:uppercase;color:#1E40AF;background:#E9EEF6;'
                f'border-radius:4px;padding:3px 9px;display:inline-block;margin-bottom:8px;">{badge}</span>'
                f'<h3 style="font-family:\'Fira Code\',monospace;font-size:15px;font-weight:600;'
                f'color:#1E3A8A;margin:0 0 12px;">{title}</h3>'
                + body_html,
                sizing_mode="stretch_width",
            ),
            styles={
                "background":    "#FFFFFF",
                "border":        "1px solid #DBEAFE",
                "border-radius": "8px",
                "box-shadow":    "0 1px 4px rgba(30,64,175,.10)",
                "padding":       "20px 24px",
                "flex":          "1 1 240px",
            },
            sizing_mode="stretch_width",
        )

    return pn.Column(
        pn.pane.HTML(
            '<div style="padding:0 0 20px;">'
            '<span style="font-family:\'Fira Code\',monospace;font-size:10px;font-weight:700;'
            'letter-spacing:.12em;text-transform:uppercase;color:#1E40AF;background:#E9EEF6;'
            'border-radius:4px;padding:3px 9px;display:inline-block;margin-bottom:10px;">'
            'Dublin · 2023</span>'
            '<h2 style="font-family:\'Fira Code\',monospace;font-size:22px;font-weight:600;'
            'color:#1E3A8A;margin:0 0 8px;">'
            'Environmental Impact on Pedestrian Footfall</h2>'
            '<p style="font-family:\'Fira Sans\',sans-serif;font-size:14px;color:#64748B;'
            'margin:0;line-height:1.6;max-width:640px;">'
            'Explores the relationship between weather, air quality, and pedestrian traffic '
            'across 20 monitoring locations in Dublin city centre throughout 2023.</p>'
            '</div>',
            sizing_mode="stretch_width",
        ),
        pn.Row(
            _info_card("Weather", "Environmental Variables", env_html),
            _info_card("Air Quality", "AQI Variables", aqi_html),
            _info_card("Footfall", "Counter Locations", loc_html),
            sizing_mode="stretch_width",
            styles={"display": "flex", "gap": "16px", "flex-wrap": "wrap",
                    "margin-bottom": "16px"},
        ),
        pn.Column(
            pn.pane.HTML(
                '<h3 style="font-family:\'Fira Code\',monospace;font-size:15px;font-weight:600;'
                'color:#1E3A8A;margin:0 0 12px;">Counter Location Map</h3>',
            ),
            map_viewer,
            styles={
                "background":    "#FFFFFF",
                "border":        "1px solid #DBEAFE",
                "border-radius": "8px",
                "box-shadow":    "0 1px 4px rgba(30,64,175,.10)",
                "padding":       "20px 24px",
            },
            sizing_mode="stretch_width",
        ),
        sizing_mode="stretch_width",
        css_classes=["dap-page"],
        styles={"padding": "24px 32px"},
    )


def createpage_1():
    parameter_column  = pn.widgets.Select(
        name="Parameter", options=list(parameters_dict.keys()),
        sizing_mode="stretch_width",
    )
    location_column = pn.widgets.Select(
        name="Location", options=list(locations),
        sizing_mode="stretch_width",
    )
    date_range_slider = pn.widgets.DateRangeSlider(
        name="Date Range",
        start=dt.datetime(2023, 1, 1),
        end=dt.datetime(2023, 12, 31, 23, 59),
        value=(dt.datetime(2023, 1, 1), dt.datetime(2023, 12, 31, 23, 59)),
        sizing_mode="stretch_width",
    )

    @pn.depends(parameter_column.param.value, location_column.param.value,
                date_range_slider.param.value)
    def update_scatter(column, location, daterange):
        return create_scatter_plot(column, location, daterange)

    return pn.Column(
        _page_header(
            "Relationship Between Variables",
            "Explore correlations between environmental / AQI parameters and pedestrian footfall.",
        ),
        pn.FlexBox(
            _chart_col(pn.Column(update_scatter, sizing_mode="stretch_width")),
            _controls_col(parameter_column, location_column, date_range_slider),
            flex_direction="row",
            flex_wrap="wrap",
            justify_content="flex-start",
            align_items="flex-start",
            sizing_mode="stretch_width",
            styles={"gap": "20px"},
        ),
        sizing_mode="stretch_width",
        css_classes=["dap-page"],
        styles={"padding": "24px 32px"},
    )


def createpage_2():
    df = get_dataset()
    return pn.Column(
        _page_header(
            "Dataset",
            'First 20 rows of the merged '
            f'<code style="{_CODE_CSS}">weather_aqi_footfall</code> table.',
        ),
        pn.Column(
            pn.pane.DataFrame(df, index=False, sizing_mode="stretch_width"),
            css_classes=["dap-table-wrap"],
            sizing_mode="stretch_width",
        ),
        sizing_mode="stretch_width",
        css_classes=["dap-page"],
        styles={"padding": "24px 32px"},
    )


def createpage_3():
    parameter_column  = pn.widgets.Select(
        name="Parameter", options=list(parameters_dict.keys()),
        sizing_mode="stretch_width",
    )
    location_column = pn.widgets.Select(
        name="Location", options=list(locations),
        sizing_mode="stretch_width",
    )
    date_range_slider = pn.widgets.DateRangeSlider(
        name="Date Range",
        start=dt.datetime(2023, 1, 1),
        end=dt.datetime(2023, 12, 31, 23, 59),
        value=(dt.datetime(2023, 1, 1), dt.datetime(2023, 12, 31, 23, 59)),
        sizing_mode="stretch_width",
    )
    toggle_group = pn.widgets.ToggleGroup(
        name="Average by",
        options=["Daily", "Weekly", "Monthly"],
        behavior="radio",
        button_type="light",
        sizing_mode="stretch_width",
    )

    @pn.depends(parameter_column.param.value, location_column.param.value,
                date_range_slider.param.value, toggle_group.param.value)
    def update_line(column, location, daterange, avgby):
        return create_line_plot(column, location, daterange, avgby)

    return pn.Column(
        _page_header(
            "Variable Distribution Over Time",
            "Compare daily / weekly / monthly averages of a weather or AQI variable "
            "against pedestrian counts at a chosen location.",
        ),
        pn.FlexBox(
            _chart_col(pn.Column(update_line, sizing_mode="stretch_width")),
            _controls_col(
                parameter_column,
                location_column,
                pn.layout.Divider(
                    margin=(8, 0, 4, 0),
                    stylesheets=["hr { border-color: #DBEAFE !important; }"],
                ),
                pn.pane.HTML(
                    f'<p style="{_SUB_H_CSS}margin-top:0;">Aggregate by</p>'
                ),
                toggle_group,
                pn.layout.Divider(
                    margin=(8, 0, 4, 0),
                    stylesheets=["hr { border-color: #DBEAFE !important; }"],
                ),
                date_range_slider,
            ),
            flex_direction="row",
            flex_wrap="wrap",
            justify_content="flex-start",
            align_items="flex-start",
            sizing_mode="stretch_width",
            styles={"gap": "20px"},
        ),
        sizing_mode="stretch_width",
        css_classes=["dap-page"],
        styles={"padding": "24px 32px"},
    )


def createpage_4():
    return pn.Column(
        _page_header("Project Report"),
        pn.pane.PDF("TeamAA.pdf", sizing_mode="stretch_width", height=780),
        sizing_mode="stretch_width",
        css_classes=["dap-page"],
        styles={"padding": "24px 32px"},
    )


# ── App assembly ───────────────────────────────────────────────────────────────
_page_creators = {
    "Introduction":              createpage_0,
    "Dataset":                   createpage_2,
    "Relationship b/w variables": createpage_1,
    "Distribution of variables": createpage_3,
    "Project Report":            createpage_4,
}

mapping    = {k: v() for k, v in _page_creators.items()}
main_area  = pn.Column(mapping["Introduction"], sizing_mode="stretch_width")


def _nav_changed(event):
    main_area.clear()
    main_area.append(mapping[event.new])


nav.param.watch(_nav_changed, "value")

dashboard = pn.template.MaterialTemplate(
    title="Dashboard — Environmental Impact on Pedestrian Footfall in Dublin",
    sidebar=[sidebar],
    main=[main_area],
    sidebar_width=280,
)

dashboard.servable()
