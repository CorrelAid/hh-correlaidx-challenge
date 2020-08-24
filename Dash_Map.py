import os
import pickle
import pandas as pd
import numpy as np
from datenguidepy import get_regions
from sklearn.preprocessing import MinMaxScaler
import geopandas as gpd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

#importing files from folder
df = pd.DataFrame(columns=['id_nuts3', 'name_nuts3', 'year'])
for f in os.listdir('data_pickles'):
    if not f.startswith('.'):
        temp = pickle.load(open('data_pickles/'+f, "rb" ))
        df = pd.merge(df, temp,  how='outer', on=['year','id_nuts3', 'name_nuts3'])
df.replace(0, np.nan, inplace = True)

# Add columns for id_nuts1 and name_nuts1
regions = get_regions()
regions_nuts1 = regions[regions.level=="nuts1"]["name"]   # Get id and names of regions on nuts1 level
df["id_nuts1"] = [str(x)[:2] for x in df.id_nuts3]   # Add column with id_nuts1
df = pd.merge(df, regions_nuts1, how='left', left_on="id_nuts1", right_index=True)  # Add column with nuts1 name
df.rename(columns=lambda x: x+"_nuts1" if x in ["id", "name"] else x, inplace=True)   # Rename column to name_nuts1

# changing location of nuts1 columns
mid = df[['id_nuts1','name_nuts1']]
df.drop(labels=['id_nuts1','name_nuts1'], axis=1, inplace = True)
df.insert(0,'name_nuts1', mid['name_nuts1'])
df.insert(0,'id_nuts1', mid['id_nuts1'])

# scaling and saving data
scaled_df = df.iloc[:,:5]
scaled_cols=MinMaxScaler().fit_transform(X=df.iloc[:,5:])
scaled_cols=pd.DataFrame(scaled_cols, columns=df.iloc[:,5:].columns)
scaled_df=pd.concat([scaled_df,scaled_cols], axis=1)

#importing json containing Lankreis borders
geojson = gpd.read_file(f'landkreise_simplify200.geojson')

# defining features for input
features = list(df.drop(['id_nuts1','name_nuts1','id_nuts3','name_nuts3','year'],axis=1).columns)

# implementing app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Graph(id='graph-with-slider',
              style= {'height': '80vh'}),
    dcc.Slider(
        id='year-slider',
        min=df['year'].min(),
        max=df['year'].max(),
        value=df['year'].min(),
        marks={str(year): str(year) for year in df['year'].unique()},
        step=None
    ),
    dcc.Checklist(
        id='feature_selection',
        options=[{'label': i, 'value': i} for i in features],
        value=features
    )
])

@app.callback(
    Output('graph-with-slider', 'figure'),
    [Input('year-slider', 'value'),
     Input('feature_selection', 'value')])

def update_figure(selected_year, selected_features):
    if len(selected_features) == 1:
        filtered_df = df[df.year == selected_year]
        filtered_df['selection'] = filtered_df[selected_features]
    else:
        filtered_df = scaled_df[scaled_df.year == selected_year]
        filtered_df['selection'] = filtered_df[selected_features].mean(axis=1)

    fig = px.choropleth_mapbox(filtered_df,
                               title="Data per Landkreis",
                               geojson=geojson,
                               color='selection',
                               color_continuous_scale="Viridis",
                               range_color=[filtered_df["selection"].min(), filtered_df["selection"].max()],
                               locations="id_nuts3",
                               featureidkey="properties.RS",
                               center={"lat": 51.1633, "lon": 10.4477},
                               animation_frame="year",
                               hover_name="name_nuts3",
                               hover_data=["name_nuts1", 'selection'],
                               mapbox_style="carto-positron",
                               zoom=4.5,
                               opacity=1)

    fig.update_layout(transition_duration=500)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)