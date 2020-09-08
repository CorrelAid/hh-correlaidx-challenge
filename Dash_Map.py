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

# importing files from folder
df3 = pd.DataFrame(columns=['id_nuts3', 'name_nuts3', 'year'])
for f in os.listdir('data_pickles'):
    if f.endswith('.pkl'):
        temp = pickle.load(open('data_pickles/'+f, "rb"))
        df3 = pd.merge(df3, temp,  how='outer', on=['year', 'id_nuts3', 'name_nuts3'])
df3.replace(0, np.nan, inplace=True)

# Add columns for id_nuts1 and name_nuts1
regions = get_regions()
regions_nuts1 = regions[regions.level=="nuts1"]["name"]   # Get id and names of regions on nuts1 level
df3["id_nuts1"] = [str(x)[:2] for x in df3.id_nuts3]   # Add column with id_nuts1
df3 = pd.merge(df3, regions_nuts1, how='left', left_on="id_nuts1", right_index=True)  # Add column with nuts1 name
df3.rename(columns=lambda x: x+"_nuts1" if x in ["id", "name"] else x, inplace=True)   # Rename column to name_nuts1

# changing location of nuts1 columns
mid = df3[['id_nuts1','name_nuts1']]
df3.drop(labels=['id_nuts1','name_nuts1'], axis=1, inplace = True)
df3.insert(0,'name_nuts1', mid['name_nuts1'])
df3.insert(0,'id_nuts1', mid['id_nuts1'])

# scaling and saving data
scaled_df3 = df3.iloc[:,:5]
scaled_cols=MinMaxScaler().fit_transform(X=df3.iloc[:,5:])
scaled_cols=pd.DataFrame(scaled_cols, columns=df3.iloc[:,5:].columns)
scaled_df3=pd.concat([scaled_df3,scaled_cols], axis=1)

# nuts1 data
df1 = df3.groupby(['id_nuts1','name_nuts1', 'year']).mean().reset_index()
scaled_df1 = df1.iloc[:,:3]
scaled_cols=MinMaxScaler().fit_transform(X=df1.iloc[:,3:])
scaled_cols=pd.DataFrame(scaled_cols, columns=df1.iloc[:,3:].columns)
scaled_df1=pd.concat([scaled_df1,scaled_cols], axis=1)


#importing json containing Landkreis borders
landkreise = gpd.read_file(f"landkreise_simplify200.geojson")
bundeslaender = gpd.read_file(f"bundeslaender_simplify200.geojson")

# defining features for input
features = sorted(list(df3.drop(['id_nuts1','name_nuts1','id_nuts3','name_nuts3','year'],axis=1).columns))

# implementing app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div([
        html.Div([
            dcc.Markdown('###### Level:'),
            dcc.RadioItems(
                id='level_selection',
                options=[{'label': 'Bundesländer', 'value':'nuts1'},
                         {'label': 'Landkreise', 'value':'nuts3'}],
                value = 'nuts3',
            ),
            dcc.Markdown('###### Variables to include:'),
            dcc.Checklist(
                id='feature_selection',
                options=[{'label': i, 'value': i} for i in features],
                value=features
            ),
        ],
            style={'width': '15%',
                   'display': 'inline-block',
                   'padding': 30,
                   'font-size':12,
                   },
        ),
        html.Div([
            dcc.Graph(id='graph-with-slider',
                      style= {'height': 800}),
            dcc.Slider(
                id='year-slider',
                min=2000,
                max=2019,
                value=2000,
                marks={str(year): str(year) for year in range(2000,2020,1)},
                step=None,
            ),
        ],
            style={'width': '80%',
                   'display': 'inline-block',
                   'float': 'right'},
        ),
    ]),
    html.Div([
        dcc.Markdown("### Variable Descriptions"),
        dcc.Markdown("###### Crime suspects <14 per 1000"),
        dcc.Markdown("Number of crime suspects from 0-13 (incl.) years in given NUTS-3 region. Includes all possible "
                     "types of crimes (please refer to this list for a full explanation of included crimes). The value "
                     "shows the negative of crimes per 1000 population (e.g. -1.4 indicates 1.4 suspects per 1000 "
                     "population in that NUTS-3 region in given year). Data is taken from BKA."),
        dcc.Markdown("###### Crime suspects 14-<18 per 1000"),
        dcc.Markdown("Number of crime suspects from 14-17 (incl.) years in given NUTS-3 region. Includes all possible "
                     "types of crimes (please refer to this list for a full explanation of included crimes). The value "
                     "shows the negative of crimes per 1000 population (e.g. -1.4 indicates 1.4 suspects per 1000 "
                     "population in that NUTS-3 region in given year). Data is taken from BKA."),
        dcc.Markdown("###### Crime victims <14 per 1000 "),
        dcc.Markdown("Number of crime victims from 0-13 (incl.) years in given NUTS-3 region. "
                     "Includes all possible types of crimes (please refer to this list for a full explanation of "
                     "included crimes). The value shows the negative of victims per 1000 population (e.g. -1.74 "
                     "indicates 1.74 victims per 1000 population in that NUTS-3 region in given year). Data is taken "
                     "from BKA."),
        dcc.Markdown("###### Crime victims 14-<18 per 1000"),
        dcc.Markdown("Number of crime victims from 14-17 (incl.) years in given NUTS-3 region. Includes all possible "
                     "types of crimes (please refer to this list for a full explanation of included crimes). The value "
                     "shows the negative of victims per 1000 population (e.g. -1.74 indicates 1.74 victims per 1000 "
                     "population in that NUTS-3 region in given year). Data is taken from BKA."),
        dcc.Markdown("###### School leavers with higher education qualification"),
        dcc.Markdown("The indicator shows what percentage of all school leavers finish school with a qualification to "
                     "continue in higher education. Data is taken from datenguidepy."),
        dcc.Markdown("###### School leavers without certificate"),
        dcc.Markdown("The indicator shows what percentage of all school leavers finish school prematurely or without a "
                     "qualification and thus have the most unfavourable prerequisites for entering job formation. The "
                     "value shows the negative (e.g. -8.8 indicates 8.8% of school leavers left without high school "
                     "certificate). Data is taken from datenguidepy.")
    ],
        style={'width': '100%',
               'display': 'block',
               'padding': 30,
               'font-size': 12},
    ),
])

@app.callback(
    Output('graph-with-slider', 'figure'),
    [Input('level_selection', 'value'),
     Input('feature_selection', 'value'),
     Input('year-slider', 'value'),
     ])
def update_figure(selected_level, selected_features, selected_year):
    if selected_level == 'nuts3':
        geojson = landkreise
        df=df3
        scaled_df=scaled_df3
    else:
        geojson = bundeslaender
        df=df1
        scaled_df=scaled_df1

    if len(selected_features) == 1:
        filtered_df = df[df.year == selected_year]
        filtered_df["selection"] = filtered_df[selected_features]
    else:
        filtered_df = scaled_df[scaled_df.year == selected_year]
        filtered_df["selection"] = filtered_df[selected_features].mean(axis=1)

    fig = px.choropleth_mapbox(filtered_df,
                               title="Data per Landkreis",
                               geojson=geojson,
                               color="selection",
                               color_continuous_scale="viridis",
                               range_color=(filtered_df["selection"].min(), filtered_df["selection"].max()),
                               locations=str("id_"+selected_level),
                               featureidkey="properties.RS",
                               center={"lat": 51.1633, "lon": 10.4477},
                               animation_frame="year",
                               hover_name=str("name_"+selected_level),
                               #hover_data={feature: True for feature in selected_features},
                               mapbox_style="carto-positron",
                               zoom=5,
                               opacity=1)

    fig.update_layout(transition_duration=5)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)