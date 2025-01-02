import pandas as pd
import os
import dash
import dash_mantine_components as dmc
from dash import html, dcc, _dash_renderer, Input, Output
import plotly.express as px

BASEDIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASEDIR, "data", "raw")
balance_file_path = os.path.join(DATA_DIR, "balance_sample.csv")
accounts_file_path = os.path.join(DATA_DIR, "accounts_sample.csv")

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
    category_orders={"type":  ['checking', 'savings', 'stocks', 'crypto']},
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
    hoverlabel=dict(font=dict(family=BODY_FONT_FAMILY, color=PLOTLY_FONT_COLOR)),
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
                                dcc.Graph(
                                    id="sunburst-plot",
                                    config=PLOTLY_CONFIG,
                                    style={"height": "100%"},
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
    Input("area-plot", "clickData"),
)
def update_sunburst(clickData):
    if clickData is None:
        selected_date = df_resampled["date"].max()
    else:
        selected_date = pd.to_datetime(clickData["points"][0]["x"])

    df_selected_date = df_resampled[df_resampled["date"] == selected_date].sort_values(['type', 'balance'])

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
        hoverlabel=dict(font=dict(family=BODY_FONT_FAMILY, color=PLOTLY_FONT_COLOR)),
        margin=dict(l=0, r=0, t=50, b=0),
        legend=dict(
            title="Account Type",
            bordercolor=LEGEND_BORDER_COLOR,
            borderwidth=1,
            font=dict(family=BODY_FONT_FAMILY, color=PLOTLY_FONT_COLOR),
        ),
    )

    return fig_pie, selected_date.strftime('%B %d, %Y')

if __name__ == "__main__":
    app.run_server(debug=True)
