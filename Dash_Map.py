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
regions_nuts1 = regions[regions.level == "nuts1"]["name"]   # Get id and names of regions on nuts1 level
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
landkreise = gpd.read_file("landkreise_simplify200.geojson")
bundeslaender = gpd.read_file("bundeslaender_simplify200.geojson")

# defining features for input
features = sorted(list(df3.drop(['id_nuts1','name_nuts1','id_nuts3','name_nuts3','year'],axis=1).columns))

# implementing app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([

    html.Div([
        dcc.Markdown("### Child Well-Being in Germany"),
        dcc.Markdown("This project was conducted in the context of the [CorrelAid](https://correlaid.org/) local chapter challenge"
                     " July - September 2020 by the [local chapter of Hamburg](https://correlaid.org/correlaid-x/hamburg/)."
                     " Contributors: Martin Wong, Vivika Wilde, Sarah Wenzel, Drenizë Rama, Long Nguyen, Trisha Nath, Christine Martens, "
                     "Mauricio Malzer, Andre Kochanke, Eva Jaumann"),
        dcc.Markdown("Germany belongs to the rich countries, nevertheless this is not a guarantee that all children and adolescents grow up in happiness."),
        dcc.Markdown("There are many different factors which contribute to the well-being of a child, main categories according to [UNICEF](https://www.unicef.org/media/files/ChildPovertyReport.pdf) are:"
                     " Material well-being"
                     ", Health and safety"
                     ", Educational well-being"
                     ", Family and peer relationships "
                     ", Behaviours and risks"
                     ", Subjective well-being"),
        dcc.Markdown("**Our goal of this project was not to calculate one single metric to evaluate happiness, but to raise awareness to"
                     " the topic and how many different factors influence children.**"),
        dcc.Markdown("**For more information please also check the [README](https://github.com/CorrelAid/hh-correlaidx-challenge/blob/master/README.md).**"),
        dcc.Markdown("#### Disclaimer"),
        dcc.Markdown("Be careful when interpreting the averages of multiple factors"),
        dcc.Markdown("The interactive map displays a standardized and normalized average across all features selected via the checkboxes."
                     " Features include information with some relation to child well-being and are intended to be selected according to the user's specific information interest"
                     " The combination of features is up to the user and the interpretation needs to be made with caution. The data has not been weighted and some factors may be over-, under- or misrepresented"
                     " Features like *population* are included for illustration purposes, even though they are not directly linked to child well-being"),
        dcc.Markdown("Also be aware that there might be data gaps - not for every year every data is available.")
    ],
        style={'width': '100%',
               'display': 'block',
               'padding': 30,
               'font-size': 12},
    ),

    html.Div([
        html.Div([
            dcc.Markdown('###### Level:'),
            dcc.RadioItems(
                id='level_selection',
                options=[{'label': 'Bundeslaender', 'value':'nuts1'},
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
        dcc.Markdown("**Some of the factors cover multiple categories, for example 'Children affected by divorce' "
                     "will not only affect the subjective, but also the material well-being.** Therefore, "
                     "consider the categorization only as a guide."),
        dcc.Markdown("#### Material well-being"),
        dcc.Markdown("###### Disposable income per inhabitant"),
        dcc.Markdown(" Average amount of money available to private households for consumption or savings per inhabitant. "
                     "Data are queried using datenguidepy."),
        dcc.Markdown("###### Recipients of minimum social security benefits"),
        dcc.Markdown("Recipients of minimum social security benefits (includes basic security in old age and gainful "
                     "employment benefit). "
                     "Value is inverted. Data is taken from datenguidepy."),
        dcc.Markdown("###### Unemployment rate"),
        dcc.Markdown("Unemployed persons as a share of the civilian labor force averaged over the year. Value is "
                     "inverted. Data is taken from datenguidepy."),



        dcc.Markdown("#### Health and safety"),
        dcc.Markdown("###### Childcare facilities"),
        dcc.Markdown("The indicator shows number of childcare facilities for 0-14 years "
                     "children in given NUTS-3 region. Data is taken from datenguidepy."),
        dcc.Markdown("###### Childcare workers per inhabitant"),
        dcc.Markdown("Number of persons working in publicly funded day care facilities for children divided by "
                     "population size. Data are queried using datenguidepy."),
        dcc.Markdown("###### Crime victims 14-<18 per 1000"),
        dcc.Markdown("Number of crime victims from 14-17 (incl.) years in given NUTS-3 region. Includes all possible "
                     "types of crimes (please refer to this list for a full explanation of included crimes). The value "
                     "shows the negative of victims per 1000 population (e.g. -1.74 indicates 1.74 victims per 1000 "
                     "population in that NUTS-3 region in given year). Data is taken from BKA."),
        dcc.Markdown("###### Crime victims <14 per 1000"),
        dcc.Markdown("Number of crime victims from 0-13 (incl.) years in given NUTS-3 region. "
                     "Includes all possible types of crimes (please refer to this list for a full explanation of "
                     "included crimes). The value shows the negative of victims per 1000 population (e.g. -1.74 "
                     "indicates 1.74 victims per 1000 population in that NUTS-3 region in given year). Data is taken "
                     "from BKA."),
        dcc.Markdown("###### Facilities for youth welfare services"),
        dcc.Markdown("The number of youth welfare facilities include facilities from "
                     "both public and private sponsors. Both facilities (excluding day care facilities for children) "
                     "include: youth work institutions, institutions of youth social work, family support institutions, common "
                     "forms of housing for mothers / fathers and children, education, youth and family advice centers, "
                     "institutions for help with education and help for young people, facilities for staff training, "
                     "facilities for young people with disabilities.  (source: datenguide)"),
        dcc.Markdown("###### Facilities with integrated childcare"),
        dcc.Markdown("The indicator shows the number of facilities with an integrated childcare in "
                     "given NUTS-3 region. Data is taken from datenguidepy."),
        dcc.Markdown("###### Hospital beds per 1000 inhabitants"),
        dcc.Markdown("How many hospital beds were set up per 1000 inhabitants on annual average. Note: a high bed density "
                     "can also result from supraregionally oriented centers (e.g. university hospitals). "
                     "Data are queried using datenguidepy."),



        dcc.Markdown("#### Educational well-being"),
        dcc.Markdown("###### Children 0-2 year in daycare(%)"),
        dcc.Markdown("The indicator shows percentage of children (0-2 years) having daycare facilities "
                     "of total children of same age group in given NUTS-3 region. Data is taken from datenguidepy."),
        dcc.Markdown("###### Children 3-5 year in care(%)"),
        dcc.Markdown("The indicator shows percentage of children (3-5 years) having daycare facilities "
                     "of total children of same age group in given NUTS-3 region. Data is taken from datenguidepy."),
        dcc.Markdown("###### School leavers with higher education qualification"),
        dcc.Markdown("The indicator shows what percentage of all school leavers finish school with a qualification to "
                     "continue in higher education. Data is taken from datenguidepy."),
        dcc.Markdown("###### School leavers without certificate"),
        dcc.Markdown("The indicator shows what percentage of all school leavers finish school prematurely or without a "
                     "qualification and thus have the most unfavourable prerequisites for entering job formation. The "
                     "value shows the negative (e.g. -8.8 indicates 8.8% of school leavers left without high school "
                     "certificate). Data is taken from datenguidepy."),


        dcc.Markdown("#### Family and peer relationships"),
        dcc.Markdown("###### Average age of local population"),
        dcc.Markdown("The indicator shows average age of local population in given NUTS-3 region. "
                     "Data is taken from datenguidepy."),
        dcc.Markdown("###### Average age of mother 1st birth"),
        dcc.Markdown("The indicator shows average age of mother at giving birth of "
                     "first child in given NUTS-3 region. Data is taken from datenguidepy."),
        dcc.Markdown("###### Child population(%)"),
        dcc.Markdown("The indicator shows percentage of children (0-17 years) of "
                     "total population in given NUTS-3 region. Data is taken from datenguidepy."),



        dcc.Markdown("#### Behaviours and risks"),
        dcc.Markdown("###### Crime suspects 14-<18 per 1000"),
        dcc.Markdown("Number of crime suspects from 14-17 (incl.) years in given NUTS-3 region. Includes all possible "
                     "types of crimes (please refer to this list for a full explanation of included crimes). The value "
                     "shows the negative of crimes per 1000 population (e.g. -1.4 indicates 1.4 suspects per 1000 "
                     "population in that NUTS-3 region in given year). Data is taken from BKA."),
        dcc.Markdown("###### Crime suspects <14 per 1000"),
        dcc.Markdown("Number of crime suspects from 0-13 (incl.) years in given NUTS-3 region. Includes all possible "
                     "types of crimes (please refer to this list for a full explanation of included crimes). The value "
                     "shows the negative of crimes per 1000 population (e.g. -1.4 indicates 1.4 suspects per 1000 "
                     "population in that NUTS-3 region in given year). Data is taken from BKA."),



        dcc.Markdown("#### Subjective well-being"),
        dcc.Markdown("###### Children affected by divorce per inhabitant"),
        dcc.Markdown(" Number of children whose parents divorced divided by population size. "
                     "Data are queried using datenguidepy. Values are inverted."),
        dcc.Markdown("###### Father in parental benefit(%)"),
        dcc.Markdown("The indicator shows information on fathers' participation in parental "
                     "benefits in given NUTS-3 region. Data is taken from datenguidepy."),
        dcc.Markdown("###### Share of sports, leisure and recreation areas in total area (%)"),
        dcc.Markdown("Share of sports, leisure and recreation areas in total area (%): “Proportion of sports, leisure and recreation areas in relation to the "
                     "total area on December 31st. The sports, leisure and recreation area is "
                     "divided by the total area and multiplied by 100.” (source: datenguide)"),

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
                               # hover_data={feature: True for feature in selected_features},
                               mapbox_style="carto-positron",
                               zoom=5,
                               opacity=1)

    fig.update_layout(transition_duration=5)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
