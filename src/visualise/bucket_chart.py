import pandas as pd
import plotly.graph_objects as go 
import plotly.express as px

from src.visualise.scatter_chart import apply_standard_graph_styling


def bucket_chart(data, x_var, y_var, y_label, hover_name_label, mean_values_list='auto'):
    if mean_values_list=='auto':
        mean_values_list = data[[y_var,x_var]].groupby(x_var).mean()[y_var].sort_values(ascending=False)      
    # Create the strip chart
    fig = px.strip(data,
                   x=x_var,
                   y=y_var, 
                   color=x_var,
                   hover_name=hover_name_label, 
                   labels={
                        y_var: y_label
                    },
                    color_discrete_sequence=px.colors.qualitative.Plotly,
                    category_orders={x_var:mean_values_list.index}).update_traces(jitter = 1)
    # Add a horizontal line for each of the category groups
    i=0.5
    for mean_value in mean_values_list:
        width = 1 / (2 * len(mean_values_list))
        fig.add_hline(y=mean_value, line_color=fig.data[int(i - 0.5)].marker.color, x0= i / len(mean_values_list) - width, x1= i / len(mean_values_list) + width,  line_width=0.7)
        i+=1
    #add vertical borders
    # Add a vertical line for each category
    for j in range(len(mean_values_list) + 1):
        fig.add_vline(x=j - 0.5, line_color="Light Grey", line_width=0.5)
    # Show the plot
    apply_standard_graph_styling(fig)
    fig.update_xaxes(tickangle=0)
    fig.update_yaxes(showgrid=False)
    fig.update_layout(width=1600, font=dict(size=20), showlegend=False, xaxis_title=None)
    return fig