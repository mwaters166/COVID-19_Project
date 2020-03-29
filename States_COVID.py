import streamlit as st
import pandas as pd
import requests
import datetime as dt
import plotly.express as px
#import sqlite3

#Streamlit Heading
st.title("US COVID-19 Data Explorer")
st.write('Project by Michele Waters')

def get_request(param="states/daily"):
    root_url="https://covidtracking.com/api/"
    url=root_url+param
    response=requests.post(url) 
    records= response.json()
    return records

#Build state dataframe
states_daily_df=pd.DataFrame(get_request())

#Get dates and change formatting
dates_df=states_daily_df['date']
states_daily_df['date']=[dt.datetime.strptime(str(date), '%Y%m%d').strftime("%m/%d/%Y") for date in dates_df.copy()]

#Get state info including full state names and fips
state_info=get_request("states/info")
unique_states= [state['name']for state in state_info] #get list of unique states
state_abbrev_dict={state['state']:[state['name'],state['fips']] for state in state_info} #get dictionary of states,abbreviations & fips
state_daily_names=[state_abbrev_dict[state][0] for state in states_daily_df['state']] #list of state names
state_daily_fips=[state_abbrev_dict[state][1] for state in states_daily_df['state']] #list of state fips
states_daily_df['state_name']=state_daily_names
states_daily_df['fips']=state_daily_fips

# #Add states_daily_df to database as states_daily
# conn=sqlite3.connect('covid19.db')
# cursor= conn.cursor()
# states_daily_df.to_sql('states_daily', conn, index_label='id', if_exists='replace')

# #Create function to query SQL data
# def query_data(sql_statement):
#     df=pd.read_sql(sql_statement, conn)
#     #cursor.execute(sql_statement)
#     return df.to_dict('records')

#Select dataset type, i.e. positive tests, negative tests, deaths, etc.
st.subheader('Select COVID-19 dataset:')
dataset_dict={"Positive tests": "positive", "Negative tests": "negative", "Total tests": "totalTestResults",
              "Daily Change in Positive Cases": "positiveIncrease","Daily Change in Negative Cases": "negativeIncrease",
              "Daily Change in Total Tests": "totalTestResultsIncrease", "Pending Tests": "pending",
              "Hospitalized": "hospitalized","Deaths": "death", "Daily Change in Deaths": "deathIncrease"}
datasets=list(dataset_dict.keys())
selected_data=st.selectbox('Data', datasets, index=0)
dataset_type=dataset_dict[selected_data] 

#Plot US state time series
def plot_state_time_series():
    st.write('Select multiple states to compare')
    selected_states=st.multiselect('State', unique_states, default=['New York', 'California', 'Washington'])
    df=states_daily_df.loc[states_daily_df['state_name'].isin(selected_states)]
    st.write('Check one box:')
    multi_plot = st.checkbox('Plot states on one graph', key='multi_state', value=True)
    indiv_plot = st.checkbox('Plot states on separate graphs', key='indiv_state')
    state_names='; '.join(selected_states)
    #Create state plots on one graph
    if multi_plot:
        st.write(f'Number of COVID-19 {dataset_type} cases over time: {state_names}')
        fig = px.line(df, x="date", y=df[dataset_type], color="state")
        fig.update_xaxes(autorange="reversed")
    #Create individual plots for each state
    elif indiv_plot:
        st.write(f'Number of COVID-19 {dataset_type} cases over time: {state_names}')
        fig = px.line(df, x=df["date"], y=df[dataset_type], color="state_name", facet_col="state", facet_col_wrap=3)
        fig.update_xaxes(autorange="reversed")
    return fig

st.subheader('Explore data by US state over time')
st.plotly_chart(plot_state_time_series()) #Graph time series in streamlit

#Create functions to round up max value to nearest thousand 
def round_up(x):
    return x if x % 1000 == 0 else x + 1000 - x % 1000

#Create function to change the color range of the heat map
counter=0
def change_range_min_max(range_min=0, range_max=round_up(int(states_daily_df[dataset_type].max()))):
    global counter
    counter+=1
    change_range = st.checkbox('Change COVID-19 population range values', key=counter)
    if change_range:
        min_range= st.slider('min range',0, range_max, value=range_min, step=50, key=counter+1)
        max_range= st.slider('max range', 0, range_max, value=range_max, step=50, key=counter+2)
        range_max= max_range
        range_min= min_range
        return [range_min, range_max]
    else:
        return [range_min, range_max]

#Plot COVID-19 cases by US state on a heat map
st.subheader('Explore data by US state geographically')

#Generates a dataframe and figure based on a date given
def generate_US_map(date='03/27/2020'):
    df=states_daily_df[states_daily_df['date']==date]
    range_col=change_range_min_max()
    fig = px.choropleth(locations=df['state'], 
                        locationmode="USA-states", color=df[dataset_type],scope="usa",
                        color_continuous_scale=px.colors.sequential.Plasma,
                        range_color=[range_col[0], range_col[1]]
                       )
                       
    return [fig, df]

date_list2=list(states_daily_df['date'].unique())[::-1] #list of unique dates, reverse order
days_index2=len(list(date_list2))-1 #length of dates list

#Get user-defined date using a slider in streamlit
date_slider2 = st.slider(f'Use the Date-Slider to see the number of US COVID-19 {dataset_type} cases over time (hover over state to see actual values):', 0, days_index2, days_index2, format="%d days since 3/04/20", key='time_US')

st.write(f"US COVID-19 {dataset_type} cases as of date: ", date_list2[date_slider2])
data=generate_US_map(date_list2[date_slider2])
fig=data[0] #figure
df=data[1] #dataframe
st.plotly_chart(fig) #Plot heatmap

#Prints the relevant dataframe in streamlit
st.subheader(f"Top 10 states for {dataset_type} cases as of date: {date_list2[date_slider2]}")
df2=df[['date', 'state_name', dataset_type]] #gets user-defined dataframe
df2=df2.sort_values(by=[dataset_type], ascending=False)[:10] #sorts dataframe by parameter, e.g. positive test and returns top10
df2.index=pd.RangeIndex(1,11)
st.table(df2) #prints table
