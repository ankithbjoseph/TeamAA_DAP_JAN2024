from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource
from bokeh.layouts import layout
from bokeh.models.widgets import Button

# Sample data
data = {'Category': ['A', 'B', 'A', 'C', 'B', 'B', 'A', 'C', 'C', 'C']}

# Function to create the count plot
def create_count_plot():
    # Prepare data
    from collections import Counter
    counts = Counter(data['Category'])
    categories = list(counts.keys())
    counts = list(counts.values())

    source = ColumnDataSource(data=dict(categories=categories, counts=counts))

    # Create a new plot
    p = figure(x_range=categories, height=250, title="Category Counts",
               toolbar_location=None, tools="")

    p.vbar(x='categories', top='counts', width=0.9, source=source)

    p.xgrid.grid_line_color = None
    p.y_range.start = 0

    return p

# Function to refresh plot
def refresh_plot():
    # This would recompute data and update the plot
    # For simplicity, here we just redraw the same plot
    plot_layout.children[1] = create_count_plot()

# Create plot and button
plot = create_count_plot()
button = Button(label="Refresh Plot", button_type="success")
button.on_click(refresh_plot)

# Arrange layout
plot_layout = layout([
    [button],
    [plot]
])

# Add the layout to the current document
curdoc().add_root(plot_layout)
