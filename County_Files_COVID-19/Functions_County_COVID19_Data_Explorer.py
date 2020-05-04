import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import plotly as py
import plotly.express as px
import time
from urllib.request import urlopen
import json

#Get US county FIPS information for plotting geographic heatmaps
def get_counties():
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
    return counties

#Update FIPS/name for Shannon/Oglala Lakota county
def update_counties(counties):
    index=-1
    for county_dict in counties['features']:
        index+=1
        if (county_dict['properties']['STATE']=="46") and (county_dict['properties']['COUNTY']=="113"):
            break
    Shannon_County=county_dict
    Oglala_Lakota=Shannon_County
    Oglala_Lakota['properties']['NAME']='Oglala Lakota'
    Oglala_Lakota['properties']['COUNTY']='102'
    Oglala_Lakota['id']='46102'
    counties['features'][1581]=Oglala_Lakota
    return counties

#Function to get COVID-19 confirmed cases & mortality data for US 
def get_data(data_set='confirmed'):
    if data_set=='confirmed':
        url="https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
        df=pd.read_csv(url)
        return [df, 'confirmed']
    elif data_set=='mortality':
        url="https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
        df=pd.read_csv(url)
        return [df, 'mortality']

#Function to return list of based on starting index of confirmed (index_c) and mortality (index_m)
def get_county_dates(county_df, dataset_type, index_c=11, index_m=12): 
    if dataset_type=='confirmed':
        index=index_c
    elif dataset_type=='mortality':
        index=index_m
    return county_df.keys()[index:]

#Get population count from JHU mortality dataset, to merge with confirmed cases dataset
def get_population_data():
    mortality_df=get_data('mortality')[0]
    population=mortality_df[['FIPS','Population']]
    return population

#Function to merge county_df with population df
def merge_population_data(county_df, population_df, dataset_type):
    if dataset_type=='confirmed':
        county_df = pd.merge(county_df, population_df, how='left', on=['FIPS'], sort=False) #add population to county data
    return county_df

#Function to reorder columns in dataframe
def reorder_column_df(df, col, new_col_index):
    col_names= list(df.columns)
    #original_index=col_names.index(col)
    new_col_names1= col_names[:new_col_index]
    new_col_names1.append(col)
    new_col_names2=col_names.copy()[new_col_index:]
    new_col_names2.remove(col)
    new_cols=new_col_names1+new_col_names2
    new_df=df.reindex(columns=new_cols)
    return new_df

#Function to remove NaN values; replace float/int with zero and replace object type with 'N/A'
def remove_na(df, col, num=0):
    if df[col].dtype=='float64' or df[col].dtype=='int64':
        df[col][df[col].isna()]=num
    elif df[col].dtype=='O':
        df[col][df[col].isna()]='N/A'
    return df

#Function to remove rows with NaN value in specific column
def remove_row_with_na_col(df, county_col):
    df=df.dropna(subset=[county_col])
    return df

#Function to primarily reorganize date columns into one column while preserving/renaming other categorical columns
def reorg_date_df(df):
    non_date_attrs = ['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Province_State', 'Country_Region', 'Lat', 'Long_', 'Combined_Key', 'Population']
    new_records=[]
    records=df.to_dict('records')
    for record in records:
        county_state=record['Combined_Key']
        state=record['Province_State']
        county=record['Admin2']
        fips=record['FIPS']
        population= record['Population']
        new_records+=[{'Date': key, 'Count': value, 'County': county, 'State': state,'County, State':county_state, 'FIPS': int(fips), 'Population': population} for key, value in record.items() if key not in non_date_attrs]
    return pd.DataFrame(new_records)

#Function to make FIPS code 5 digits, and fill zeros to the left if less than 5 digits
def convert_FIPS(df, fips_col='FIPS'):
    df[fips_col] = df[fips_col].apply(lambda x: str(int(x)).zfill(5)) #fill zeroes to the left, to make 5 digit FIPS columns for plotting
    return df

#Function to convert dates to datetime 
def format_date(df, date_col='Date'):
    df[date_col] = pd.to_datetime(df[date_col]) #convert dates to datetime
    df[date_col]=df[date_col].astype('datetime64').apply(lambda x: x.strftime('%b %d, %Y') )#return date in specified format, i.e. 'Apr 3, 2020'
    return df

#Function to get COVID-19 Log10(counts) and replace all 0 count values with 0 (for plotting display)
def log_counts_df(df, count_col='Count'):
    counts=df[count_col]
    log_count=[]
    for count in counts:
        if count==0:
            log_count.append(0)
        else:
            log_count.append(np.log10(count))
    df['log_counts']=log_count
    return df

#Function to change specific values in a column
def clean_col(df, col, original_val, new_val):
    new_col=[]
    for row in df[col]:
        if row==original_val:
            row=new_val
        else:
            row=row
        new_col.append(row)
    df[col]=new_col
    return df

#Function to filter values from column in a dataframe
def filter_min_val(df, col, threshold=1, kind='min'):
    if kind=='min':
        df=df.loc[list(df[df[col]>threshold].index)]
    if kind=='max':
        df=df.loc[list(df[df[col]<threshold].index)]
    return df

#Function to add counts/per 100K people to data frame for plotting and normalization
def counts_per_100K_df(df, count_col='Count', pop_col='Population'):
    counts=df[count_col]
    df['count_per_100K_people']=round(df[count_col]/(df[pop_col]/100000))
    return df

#Function to get abbreviated date list
def get_selected_dates(records_df, date_col='Date', begin_index=37, end_index=None):
    sel_dates=list(records_df[date_col].unique())[begin_index:end_index] 
    return sel_dates

#Function to generate unique id keys for plotting/streamlit widgets
key_id = 1
def generate_key_id():
    global key_id
    stored_id = key_id
    key_id += 1
    return stored_id

#Function to return daily count message
def get_daily_count(df, dataset_type, count_col='Count', date_col='Date', return_date=None, kind='US'):
    if return_date==None:
        return_date=list(df[date_col])[-1]
    total_cases=df[df[date_col]==return_date][count_col].sum()
    return f"The total number of {dataset_type} cases in {kind} as of {return_date} is: {total_cases}"

#Choose map type, i.e. static or weekly/time series heatmap for all US counties using plotly choropleth and streamlit
def select_map_type(records_df, dates, dataset_type, counties, kind='US'):
    st.subheader('Select static or weekly time series map:')
    st.write('Check one box:')
    static_plot = st.checkbox(f'Create static {kind} heat map (choose one date on the drop-down calendar)', key=f"{kind}_static_map", value=True)
    time_plot = st.checkbox(f'Create weekly time series {kind} heat map (choose time step & press the play button)', key=f"{kind}_time_map")
    #Display county data on US static map
    if static_plot:
        date_input = st.date_input(f"Pick a date between {dates[0]} and {dates[-1]}", dt.datetime.strptime(dates[-1], '%b %d, %Y'), key=f"{kind}_time_input")
        converted_date=dt.datetime.strftime(date_input, '%b %d, %Y') 
        date_index=dates.index(converted_date)
        table_date=converted_date
        df=records_df[records_df['Date']==converted_date]
        if kind !='US':
            df=df[df['State']==kind]
        total_cases=df['Count'].sum()
        st.write(f"{kind} COVID-19 {dataset_type} cases as of date: ", converted_date)
        st.write(f"Total Cases: {total_cases}")
        an_frame=None
        an_group=None
    #Display county data on US time series map
    elif time_plot:
        time_steps={'Five days': 5, 'Weekly':7, 'Bi-weekly':14, 'Monthly':28}
        time_type=list(time_steps.keys())
        selected_step=st.selectbox('Choose a time step', time_type, index=2, key=f"{kind}time_step") #user selection
        selected_dates= dates[::-1*time_steps[selected_step]][::-1] #dates[::-7][::-1]
        table_date=selected_dates[-1]
        df=records_df[(records_df['Date'].isin(selected_dates))]
        if kind !='US':
            df=df[df['State']== kind]
        total_cases=df[df['Date']==table_date]['Count'].sum()
        st.write(f"{kind} COVID-19 {dataset_type} cases from {selected_dates[0]} to {selected_dates[-1]}")
        an_frame='Date'
        an_group='Date'
        st.write(f"Total Cases {selected_dates[-1]}: {total_cases}")
    fig = px.choropleth(df, geojson=counties, locations='FIPS', color='log_counts',
                               color_continuous_scale=py.colors.sequential.Jet,
                               range_color=(0, df['log_counts'].max()),
                               scope='usa',
                               hover_name='County',
                               hover_data=['Count', 'State'],
                               labels={'Count':'Number of cases', 'log_counts': 'Log10(Count)'},
                               animation_frame=an_frame, 
                               animation_group=an_group, 
                               title='COVID-19 Cases'
                        )
    fig.update_layout(coloraxis_colorbar=dict(title='Count',tickvals = [0, 1, 2, 3, 3.699, 4, 4.301, 5, 5.301, 5.699, 6],ticktext = ['1', '10', '100', '1,000', '5,000','10,000', '20,000', '100,000', '200,000', '500,000', '1,000,000'] ))
    if kind !='US':
        fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return [fig, df, table_date]

#Function to plot COVID count vs. time for individual counties given a dataframe
def plot_top_count_vs_time(df, dataset_type, date_col='Date', count_col='Count', county_state_col='County, State', kind='US', ):
    st.subheader(f"Current Top 10 counties for COVID-19 in {kind} for {dataset_type} cases over time")
    fig = px.line(df, x=date_col, y=count_col, color=county_state_col, width=800, height=600) #line plot
    fig.update_layout(xaxis=dict(rangeslider=dict(visible=True))) #adds range slider for x-axis
    return fig

#Function to plot subplots of all US cases, Top 10 states, and Top 10 counties (for current) date vs time
def plot_top_US_county_state(records_df, dates, dataset_type):
    st.subheader(f"COVID-19 {dataset_type} cases in US, Top 10 states, & Top 10 counties v. time")
    US_agg_df=records_df.groupby(['Date'], as_index=False).sum().sort_values(by='Count', ascending=True)
    state_agg_df=records_df.groupby(['State', 'Date'], as_index=False).sum().sort_values(by='Count', ascending=True)
    top_ten_states=list(state_agg_df[state_agg_df['Date']==dates[-1]][-10:]['State'].unique())
    top_ten_counties= list(records_df[records_df['Date']==dates[-1]].sort_values(by='Count', ascending=True)[-10:]['County, State'].unique())
    fig1= px.scatter(US_agg_df, x='Date', y='Count', title='US cases vs. time', color_discrete_sequence=px.colors.sequential.Inferno)
    fig2= px.scatter(state_agg_df[state_agg_df['State'].isin(top_ten_states)], x='Date', y='Count', color='State', title='State cases vs. time', color_discrete_sequence=px.colors.cyclical.HSV[1:])
    fig3= px.scatter(records_df[records_df['County, State'].isin(top_ten_counties)], x='Date', y='Count', color='County, State') #line plot
    fig= py.subplots.make_subplots(rows=1, cols=3)
    fig.append_trace(fig1['data'][0], row=1, col=1)
    for trace in fig2['data']:
        fig.append_trace(trace, row=1, col=2)
    for trace in fig3['data']:
        fig.append_trace(trace, row=1, col=3)

    fig.update_layout(height=500, width=1200, title_text='''  United States                                  Top 10 States                        Top 10 Counties w/ COVID-19 Cases''')
    return fig

#Function to return a dataframe of top ten counties by date
def get_top_ten_counties_by_date(county_df, date, state=None):
    if state==None:
        top_ten=county_df.sort_values(by=date, ascending=False)[:10]
    else:
        top_ten=county_df[county_df['Province_State']==state].sort_values(by=date, ascending=False)[:10]
    return top_ten

#Function to print 'Top 10 Counties' Table 
def return_top_table(df, table_date, dataset_type, kind='US', one_date=True):
    st.subheader(f"Top 10 counties in {kind} for {dataset_type} cases as of date: {table_date}")
    if one_date:
        df=df[df['Date']==table_date]
    df=df[df['Population'] != 0] #filter out invalid population/non-county data
    df=df[['Date','County, State', 'Population', 'count_per_100K_people', 'Count']] #gets user-defined dataframe
    count_dict={"Total COVID-19 Count": "Count", "COVID-19 Count per 100K People (based on county population)": "count_per_100K_people", "County Population": "Population"}
    count_options=list(count_dict.keys()) #options for count table display
    count_data=st.selectbox('Sort by:', count_options, index=0, key=f"{kind}_sort_option") #user selection of sort options
    df=df.sort_values(by=[count_dict[count_data]], ascending=False)[:10] #sorts dataframe by parameter, e.g. positive test and returns top10
    df.index=pd.RangeIndex(1,11)
    return df 

#Function to plot COVID count vs. time for individual counties given a dataframe
def plot_counties_vs_time(df, dataset_type, default, date_col='Date', count_col='Count', county_state_col='County, State', kind='US'):
    st.subheader(f"Select counties in {kind} for {dataset_type} cases over time")
    if kind !='US':
        df=df[df['State']== kind]
    unique_states_counties= list(df[county_state_col].unique())
    selected_counties=st.multiselect('County', unique_states_counties, default=default)
    select_counties_df=df.loc[df[county_state_col].isin(selected_counties)]
    fig = px.line(select_counties_df, x=date_col, y=count_col, color=county_state_col, width=800, height=600) #line plot
    fig.update_layout(xaxis=dict(rangeslider=dict(visible=True))) #adds range slider for x-axis
    return fig