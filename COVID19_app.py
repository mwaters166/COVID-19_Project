#Import modules
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import datetime as dt
import sqlite3
conn=sqlite3.connect('covid19.db')
cursor= conn.cursor()

#Streamlit Heading
st.title("COVID-19 Data Explorer")
st.write('Project by Michele Waters')
st.subheader('Explore data by country over time')

#Select one of three COVID-19 Data sets
def select_data():
    st.write('Select the data you would like to explore (only check one box):')
    confirmed_data=st.checkbox('COVID-19 Confirmed Cases', key='c', value=True)
    recovered_data=st.checkbox('COVID-19 Recovered Cases', key='r')
    mortality_data=st.checkbox('COVID-19 Mortality', key='m')
    if confirmed_data:
        url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
        return [url, "confirmed"]
    elif recovered_data:
        url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv"
        return [url, "recovered"]
    elif mortality_data:
        url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
        return [url, "mortality"]
url_data=select_data()
url= url_data[0]
dataset_type=url_data[1]
df = pd.read_csv(url) #create dataframe
date_records = df.to_dict('records') #create list of dictionaries

#Populate list 'records' with dictionaries of non-date attributes and dates 
records = []
non_date_attrs = ['Country/Region', 'Lat', 'Long', 'Province/State']
for date_record in date_records:
    country = date_record['Country/Region']
    state = date_record['Province/State']
    latitude= date_record['Lat']
    longitude= date_record['Long']
    records+= [{'date': date, 'confirmed_count': count, 'country': country, 'state': state, 'latitude': latitude, 'longitude':longitude } for date, count in list(date_record.items()) if date not in non_date_attrs]
records_df = pd.DataFrame(records) #create dataframe
records_df['date'] = pd.to_datetime(records_df['date']) #convert dates to datetime

#Create SQL table of country data with transposed dates from records
conn=sqlite3.connect('covid19.db')
cursor= conn.cursor()
records_df.to_sql('covid_date_T', conn, index_label='id', if_exists='replace')

#Create function to query SQL data
def query_data(sql_statement):
    df=pd.read_sql(sql_statement, conn)
    #cursor.execute(sql_statement)
    return df.to_dict('records')

#Function to return COVID-19 cases by country
def find_data_by_country():
    return query_data('SELECT SUM(confirmed_count) as count, country, date FROM covid_date_T GROUP BY country, date')

#Create list of countries and create dataframe based on user selection
country_df=pd.DataFrame(find_data_by_country())
country_df['date'] = pd.to_datetime(country_df['date']) #convert dates to datetime
countries= list(sorted(set(country_df["country"]))) #create unique list of countries

#Plot time series for multiple countries using plotly
def plot_time_series():
    st.write('Select multiple countries to compare:')
    selected_countries=st.multiselect('Country or Region', countries, default=['US','China', 'Italy', 'Korea, South'])
    df=country_df.loc[country_df['country'].isin(selected_countries)]
    multi_plot = st.checkbox('Plot countries on one graph', key='multi', value=True)
    indiv_plot = st.checkbox('Plot countries on separate graphs', key='indiv')
    country_names='; '.join(selected_countries)
    if indiv_plot:
        st.write(f'Number of COVID-19 {dataset_type} cases over time: {country_names}')
        fig = px.line(df, x="date", y="count", color="country", facet_col="country", facet_col_wrap=3)
        return fig
    elif multi_plot:
        st.write(f'Number of COVID-19 {dataset_type} cases over time: {country_names}')
        fig = px.line(df, x="date", y="count", color="country")
        return fig
        
st.plotly_chart(plot_time_series())
        
#Plot COVID-19 cases by country on a heat map
st.subheader('Explore data by country geographically')
#Query and join iso code for each country and create dataframe
country_isos = pd.read_csv('./Country_iso.csv', index_col=False)
country_isos.to_sql('country_isos', conn, index_label='id', if_exists='replace') #create table of country isos
country_iso_df=pd.DataFrame(query_data('''SELECT country, country_isos.iso, SUM(confirmed_count) as count, date FROM covid_date_T 
                JOIN country_isos ON covid_date_T.country=country_isos."Country/Region"
                GROUP BY covid_date_T.country, covid_date_T.date'''))

#Create function to change the color range of the heat map
counter=0
def change_range_color(range_max=20000):
    global counter
    counter+=1
    change_range = st.checkbox('Change COVID-19 population range values', key=counter)
    if change_range:
        min_range= st.slider('min range',0, range_max, value=0, step=int(range_max/200), key=counter+1)
        max_range= st.slider('max range', 0, range_max, value=range_max, step=int(range_max/200), key=counter+2)
        range_color=[min_range,max_range]
        return range_color
    else:
        range_color=[0,range_max]
        return range_color

#Generate global heat map
def generate_map(df):
    fig = px.choropleth(df, locations="iso",
                        color="count",
                        hover_name="country", # column to add to hover information
                        color_continuous_scale=px.colors.sequential.Plasma,
                        range_color=change_range_color())
    return fig

date_list=list(sorted(set(country_iso_df['date']))) #list of dates
days_index=len(list(date_list))-1 #length of dates list
datetime_list=[dt.datetime.strptime(date, '%Y-%m-%d %H:%M:%S') for date in date_list]
date_slider = st.slider(f'Use the Date-Slider to see the number of global COVID-19 {dataset_type} cases over time (hover over countries to see actual values):', 0, days_index, days_index, format="%d days since 1/22/20", key='time_global') #user select date
df=country_iso_df[country_iso_df['date']==date_list[date_slider]] #create dataframe from user-selected date
date_formatted=dt.datetime.strftime(datetime_list[date_slider], '%m/%d/%Y') #format date
st.write(f"Global COVID-19 {dataset_type} cases as of date: ", date_formatted) #display formatted date
st.plotly_chart(generate_map(df)) #plot on map

#Prints the relevant dataframe in streamlit
st.subheader(f"Top 10 countries for {dataset_type} cases as of date: {date_formatted}")
df2=df[['country', 'count']] #gets user-defined dataframe
df2=df2.sort_values(by='count', ascending=False) #sorts dataframe by parameter, e.g. positive test
df2=df2.reset_index(drop=True)[:10] #gets top 10 
st.table(df2) #prints table

''' 
Note: the subsequent code was written based on formatting of archived JHU data sets, which originally contained US
state data. The archived data can be found at the following link:
https://github.com/CSSEGISandData/COVID-19/tree/master/archived_data/archived_time_series.
'''

# #Select state data
# st.subheader('Explore data by US state over time')
# states_url = "https://secure.ssa.gov/apps10/poms.nsf/lnx/0901501010"
# state_dfs = pd.read_html(states_url, header=0)[0]
# state_dfs.to_sql('states', conn, index_label='id', if_exists='replace') #create table of state abbreviations

# #Function to return US data by state (aggregated) or by county for each state
# def find_data_by_US_state():
#     records=query_data('''SELECT SUM(confirmed_count) as count, covid_date_T.state, states."Territory Abbreviation" as st_abbrev, country, date FROM covid_date_T
#                       LEFT JOIN states ON covid_date_T.state=states.State
#                       GROUP BY covid_date_T.state, date
#                       HAVING country=="US"''')
#     state_data=[]
#     state_data+=[record for record in records if "," not in record['state']]
#     return state_data
# US_state_df=pd.DataFrame(find_data_by_US_state())

# #Plot US state time series
# unique_states=sorted(list(set((US_state_df['state']))))
# def plot_state_time_series():
#     st.write('Select multiple states to compare')
#     selected_states=st.multiselect('State', unique_states, default=['Diamond Princess','New York', 'California', 'Washington'])
#     df=US_state_df.loc[US_state_df['state'].isin(selected_states)]
#     multi_plot = st.checkbox('Plot states on one graph', key='multi_state', value=True)
#     indiv_plot = st.checkbox('Plot states on separate graphs', key='indiv_state')
#     state_names='; '.join(selected_states)
#     if indiv_plot:
#         st.write(f'Number of COVID-19 {dataset_type} cases over time: {state_names}')
#         fig = px.line(df, x="date", y="count", color="state", facet_col="state", facet_col_wrap=3)
#         #fig.layout.yaxis3.update(matches=None)
#         return fig
#     elif multi_plot:
#         st.write(f'Number of COVID-19 {dataset_type} cases over time: {state_names}')
#         fig = px.line(df, x="date", y="count", color="state")
#         #fig.layout.yaxis.update(matches=None)
#         return fig
       
# st.plotly_chart(plot_state_time_series())

# #Plot COVID-19 cases by US state on a heat map
# st.subheader('Explore data by US state geographically')
# def generate_US_map(date='2020-03-19 00:00:00'):
#     df=US_state_df[US_state_df['date']==date]
#     fig = px.choropleth(locations=df['st_abbrev'], 
#                         locationmode="USA-states", color=df['count'],                 scope="usa",color_continuous_scale=px.colors.sequential.Plasma,range_color=change_range_color(3000))
#     return fig
# date_list2=list(sorted(set(country_iso_df['date'])))[47:] #list of dates
# days_index2=len(list(date_list2))-1 #length of dates list
# datetime_list2=[dt.datetime.strptime(date, '%Y-%m-%d %H:%M:%S') for date in date_list2]
# date_slider2 = st.slider(f'Use the Date-Slider to see the number of US COVID-19 {dataset_type} cases over time (hover over state to see actual values):', 0, days_index2, days_index2, format="%d days since 3/09/20", key='time_US')
# date_formatted2=dt.datetime.strftime(datetime_list2[date_slider2], '%m/%d/%Y')
# st.write(f"US COVID-19 {dataset_type} cases as of date: ", date_formatted2)
# st.plotly_chart(generate_US_map(date_list2[date_slider2]))

