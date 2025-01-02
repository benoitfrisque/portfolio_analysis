import pandas as pd
import os
import dash
import dash_mantine_components as dmc
from dash import html, dcc, _dash_renderer
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
    .reset_index()
)

# Merge the accounts data to get the account type
df_resampled = df_resampled.merge(accounts, on="account")

# Stacked area plot
fig = px.area(
    df_resampled,
    x="date",
    y="balance",
    color="type",
    line_group="account",
    category_orders={"type": ["checking", "savings", "stocks", "crypto"]},
    title="Total Portfolio Value Over Time",
    template="plotly_white",
    color_discrete_sequence=COLOR_PALETTE,
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Balance",
    yaxis_ticksuffix="€",
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    font_color=PLOTLY_FONT_COLOR,
    font=dict(family=BODY_FONT_FAMILY),
    hoverlabel=dict(
        font=dict(
            family=BODY_FONT_FAMILY,
            color=PLOTLY_FONT_COLOR
            )
        ),
    margin=dict(l=0, r=0, t=50, b=0),
    legend=dict(
        title="Account Type",
        bordercolor=LEGEND_BORDER_COLOR,
        borderwidth=1,
        font=dict(family=BODY_FONT_FAMILY, color=PLOTLY_FONT_COLOR),
    ),
)


# Create a Dash application
_dash_renderer._set_react_version("18.2.0")
app = dash.Dash(__name__)


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
                        dcc.Graph(figure=fig, config=PLOTLY_CONFIG),
                    ],
                    pt="md",
                    pb="cs",
                    shadow="sm",
                    withBorder=True,
                ),
            ],
            style={"padding": "1rem"},
        ),
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True)
