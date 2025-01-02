import pandas as pd
import os
import dash
import dash_mantine_components as dmc
from dash import html, dcc, _dash_renderer, Input, Output
import plotly.express as px

BASEDIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASEDIR, "data", "raw")
balance_file_path = os.path.join(DATA_DIR, "balance.csv")
accounts_file_path = os.path.join(DATA_DIR, "accounts.csv")

COLOR_PALETTE = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51"]
BODY_FONT_FAMILY = "'Source Sans Pro', sans-serif"
PLOTLY_FONT_COLOR = "#545b61"  # Grey
LEGEND_BORDER_COLOR = "#dee2e6"  # Light grey

PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


df = pd.read_csv(balance_file_path)
accounts = pd.read_csv(accounts_file_path)

df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
df = df.sort_values(by=["account", "date"], ignore_index=True)
df.set_index("date", inplace=True)

# Resample the data to daily frequency and interpolate missing values
df_resampled = (
    df.groupby("account")
    .resample("1D")
    .mean()
    .interpolate(method="linear")
    .round(2)
    .reset_index()
)

# Merge the accounts data to get the account type
df_resampled = df_resampled.merge(accounts, on="account")

# Capitalize the account types
df_resampled["type"] = df_resampled["type"].str.capitalize()

# Stacked area plot
COLOR_PALETTE = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51"]
BODY_FONT_FAMILY = "'Source Sans Pro', sans-serif"
PLOTLY_FONT_COLOR = "#545b61" # Grey
LEGEND_BORDER_COLOR = "#dee2e6" # Light grey


# Stacked area plot
fig_area = px.area(
    df_resampled,
    x="date",
    y="balance",
    color="type",
    line_group="account",
    category_orders={"type":  ['Checking', 'Savings', 'Stocks', 'Crypto']},
    template="plotly_white",
    color_discrete_sequence=COLOR_PALETTE,
)

fig_area.update_layout(
    xaxis_title="",
    yaxis_title="Balance",
    yaxis_ticksuffix='€',
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    font_color=PLOTLY_FONT_COLOR,
    font=dict(family=BODY_FONT_FAMILY),
    hoverlabel=dict(font=dict(family=BODY_FONT_FAMILY)),
    margin=dict(l=0, r=0, t=50, b=0),
    legend=dict(
        title="Account Type",
        orientation="h",  # Horizontal orientation
        x=0.5,            # Center horizontally
        y=1,            # Position above the plot area
        xanchor="center", # Align center of the legend
        yanchor="bottom", # Align bottom of the legend
    ),
)

# Filter data to show only the last year
one_year_ago = pd.Timestamp.now() - pd.DateOffset(years=1)
df_last_year = df_resampled[df_resampled["date"] >= one_year_ago]

df_last_year_total = df_last_year.groupby("date")["balance"].sum().reset_index()

# Line plot for the last year total
fig_last_year = px.line(
    df_last_year_total,
    x="date",
    y="balance",
    template="plotly_white",
    color_discrete_sequence=COLOR_PALETTE,
)

fig_last_year.update_layout(
    xaxis_title="Date",
    yaxis_title="Total Balance (Last Year)",
    yaxis_ticksuffix='€',
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    font_color=PLOTLY_FONT_COLOR,
    font=dict(family=BODY_FONT_FAMILY),
    hoverlabel=dict(font=dict(family=BODY_FONT_FAMILY)),
    margin=dict(l=0, r=0, t=50, b=0),
)

# Create a Dash application
_dash_renderer._set_react_version("18.2.0")

external_stylesheets = [
    # dmc.styles.ALL,
    dmc.styles.DATES,
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = dmc.MantineProvider(
    theme={
        "fontSmoothing": True,
        "fontFamily": BODY_FONT_FAMILY,
        "defaultRadius": "md",  # Default radius for cards
    },
    children=[
        html.Div(
            [
                dmc.Title("Portfolio Dashboard", order=2),
                dmc.Card(
                    [
                        dmc.Title("Total Balance (Last Year)", order=3),
                        dcc.Graph(
                            id="last-year-plot",
                            figure=fig_last_year,
                            config=PLOTLY_CONFIG,
                            style={"height": "100%"},
                        ),
                    ],
                    p="md",
                    shadow="sm",
                    withBorder=True,
                    w="95%",
                    h="500px",
                    style={"marginTop": "20px"},
                ),
                dmc.Group(
                    [
                        dmc.Card(
                            [
                                dmc.Title("Total Portfolio Value over Time", order=3),
                                dcc.Graph(
                                    id="area-plot",
                                    figure=fig_area,
                                    config=PLOTLY_CONFIG,
                                    style={"height": "100%"},
                                ),
                            ],
                            pt="md",
                            pb="cs",
                            shadow="sm",
                            withBorder=True,
                            w="65%",
                            h="500px",
                        ),
                        dmc.Card(
                            [
                                dmc.Title("Portfolio Composition", order=3),
                                html.Div(
                                    [
                                        dmc.Text("Selected Date:", style={"marginRight": "10px"}),
                                        dmc.Badge(id="selected-date", variant="outline", color="blue", size="lg"),
                                    ],
                                    style={"display": "flex", "alignItems": "center", "marginBottom": "10px"},
                                ),
                                dmc.Alert(
                                    id="negative-values-alert",
                                    title="Warning, some accounts have negative values and are ignored here!",
                                    color="yellow",
                                    style={"display": "none"},
                                ),
                                dcc.Graph(
                                    id="sunburst-plot",
                                    config=PLOTLY_CONFIG,
                                    style={"height": "350px"},
                                ),

                            ],
                            p="md",
                            shadow="sm",
                            withBorder=True,
                            w="30%",
                            h="500px",
                        ),
                    ],
                    align="stretch",
                ),

            ],
            style={"padding": "1rem"},
        ),
    ],
)

@app.callback(
    Output("sunburst-plot", "figure"),
    Output("selected-date", "children"),
    Output("negative-values-alert", "style"),
    Input("area-plot", "clickData"),
    Input("last-year-plot", "clickData"),
)
def update_sunburst(clickData_area, clickData_last_year):
    if clickData_area is None and clickData_last_year is None:
        selected_date = df_resampled["date"].max()
    elif clickData_area is not None:
        selected_date = pd.to_datetime(clickData_area["points"][0]["x"])
    else:
        selected_date = pd.to_datetime(clickData_last_year["points"][0]["x"])

    df_selected_date = df_resampled[df_resampled["date"] == selected_date].sort_values(['type', 'balance'])
    negative_values = df_selected_date[df_selected_date["balance"] < 0]
    df_selected_date = df_selected_date[df_selected_date["balance"] > 0]  # Remove negative values

    fig_pie = px.sunburst(
        df_selected_date,
        path=["type", "account"],
        values="balance",
        template="plotly_white",
        color_discrete_sequence=COLOR_PALETTE,
    )

    fig_pie.update_traces(textinfo="label+percent root")

    fig_pie.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        font=dict(family=BODY_FONT_FAMILY),
        hoverlabel=dict(font=dict(family=BODY_FONT_FAMILY)),
        margin=dict(l=0, r=0, t=50, b=0),
        legend=dict(
            title="Account Type",
            bordercolor=LEGEND_BORDER_COLOR,
            borderwidth=1,
            font=dict(family=BODY_FONT_FAMILY, color=PLOTLY_FONT_COLOR),
        ),
    )

    alert_style = {"display": "none"}
    if not negative_values.empty:
        alert_style = {"display": "block"}

    return fig_pie, selected_date.strftime('%B %d, %Y'), alert_style

if __name__ == "__main__":
    app.run_server(debug=True)
