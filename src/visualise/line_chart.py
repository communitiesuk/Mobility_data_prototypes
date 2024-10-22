import pandas as pd
import plotly.graph_objects as go 
import plotly.express as px
import matplotlib.pyplot as plt

from src.utils.constants import diverging_colour_scale
from src.utils.constants import map_lu_partnership_colour_scale_unordered


def apply_standard_graph_styling(fig: go.Figure) -> None:
    """
    Apply standard styling to a plotly graph.
    fig: plotly.graph_objs.Figure -- The graph figure to style
    """
    fig.update_layout(
        xaxis={"showgrid": False},
        height=650,
        paper_bgcolor="white",
        plot_bgcolor="white",
    )

    fig.update_layout(font=dict(size=22), xaxis_title=None)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="LightGrey")
    fig.update_layout(font_family="Arial")

    # add space between y axis labels and y axis (avoid overlap with left most x axis label)
    fig.update_layout(margin=dict(pad=20))


def apply_standard_linegraph_styling(fig: go.Figure) -> None:
    """
    Apply standard styling to a plotly line graph.
    fig: plotly.graph_objs.Figure -- The graph figure to style
    """
    apply_standard_graph_styling(fig)
    fig.update_traces(line={"width": 4})
    # fig.update_traces(mode='markers+lines')
    # fig.update_traces(marker={"size": 10})
    fig.update_layout(legend={"traceorder": "reversed"})

    # reverse line layering (first line is on top of second line, etc.)
    fig.data = fig.data[::-1]

    fig.update_xaxes(tickangle=0)


def line_chart(data: pd.DataFrame, fig_title: str="", x_col: str="date", y_col: str="indexed_value", x_lab: str="date", y_lab: str="indexed_value", colour_col: str=None, colour_col_label: str=None) -> go.Figure:
    fig = px.line(
        data,
        x=x_col,
        y=y_col,
        color=colour_col,
        color_discrete_sequence=map_lu_partnership_colour_scale_unordered,
        title=fig_title,
        height=750,
        labels={
            x_col: x_lab,
            y_col: y_lab,
            colour_col: colour_col_label
        },
    )
    apply_standard_linegraph_styling(fig)
    return fig


def add_average_line(data, fig):
    fig.add_shape(type='line',
                x0=data['date'].min(),
                y0=data['indexed_value'].mean(),
                x1=data['date'].max(),
                y1=data['indexed_value'].mean(),
                line=dict(color='Red',),
                xref='x',
                yref='y',
    )
    return fig


def add_outliers(fig, anomalies):
    fig.add_trace(go.Scatter(x=anomalies.index,
                            y = anomalies,
                            mode = 'markers',
                            name = 'Outliers'))
    fig.update_traces(marker={'size': 15})
    return fig