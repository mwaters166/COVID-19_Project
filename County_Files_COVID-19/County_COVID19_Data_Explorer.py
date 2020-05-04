import Functions_County_COVID19_Data_Explorer
from Functions_County_COVID19_Data_Explorer import *
import streamlit as st

#Streamlit Heading
st.title("US Counties COVID-19 Data Explorer")
st.write('Project by Michele Waters; based on data compiled by Johns Hopkins University: https://github.com/CSSEGISandData/COVID-19')

####################
#All US County Data
st.subheader('Explore Data: All United States Counties')

#Get US county FIPS information for plotting geographic heatmaps
counties=get_counties()
counties=update_counties(counties)

#Select data from user input, i.e. confirmed COVID-19 cases or mortality data
st.subheader('Select COVID-19 dataset:')
dataset_dict={"Confirmed Cases": "confirmed", "Mortality": "mortality"}
datasets=list(dataset_dict.keys()) #data set names displayed
selected_data=st.selectbox('Data', datasets, index=0, key='select_data') #user selection
dataset_type=dataset_dict[selected_data] #underlying dataset names
county_data=get_data(dataset_type) #confirmed count data; can also be set to 'mortality'
county_df= county_data[0] #return dataframe of county data from get_data function
dataset_type=county_data[1]

#Get list of all dates from data
all_dates=get_county_dates(county_df, dataset_type=dataset_type)

#Get population count from JHU mortality dataset, to merge with confirmed cases dataset
population_df=get_population_data()

#Function to merge county_df with population df
county_df=merge_population_data(county_df, population_df, dataset_type)

#Reorder population column
county_df=reorder_column_df(county_df, "Population", 11)

#Remove NaN values; replace float/int with zero and replace object type with 'N/A'
county_df=remove_na(county_df, 'FIPS')
county_df=remove_na(county_df, 'UID')
county_df=remove_na(county_df, 'Lat')
county_df=remove_na(county_df, 'Long_')

#Remove rows with no county information 
county_df=remove_row_with_na_col(county_df, 'Admin2')

##Get a dataframe of all counties, with reorganized date column, 5 digit FIPS codes, dates in datetime format, log
records_df=reorg_date_df(county_df) #reorganize dates
records_df=convert_FIPS(records_df) #change FIPS to 5 digits
records_df=format_date(records_df)  #convert Date column to datetime
records_df=log_counts_df(records_df) #add count column converted to Log10
records_df=clean_col(records_df, "Population", 0, 1) #Change counties with population listed as zero to 1, to avoid divide by zero 
records_df=counts_per_100K_df(records_df) #Add counts/per 100K people to data frame for plotting and normalization

#Get list of unique dates, starting Feb 28, 2020 for plotting on heatmap
dates=get_selected_dates(records_df, begin_index=37, end_index=None) #suggested: begin_index=37 (i.e. February 28)

#Plot static or weekly/time series heatmap for all US counties using plotly choropleth and streamlit
US_data=select_map_type(records_df=records_df, dates=dates, dataset_type=dataset_type, counties=counties, kind='US') #returns return list with figure, dataframe, and date used for table
US_figure=US_data[0]
US_df=US_data[1]
st.plotly_chart(US_figure)

#Return statement with today's total case count
st.write(get_daily_count(df=US_df, dataset_type=dataset_type, count_col='Count', date_col='Date', return_date=None))

#Filter out min values from population column
US_df=filter_min_val(df=US_df, col='Population', threshold=1, kind='min')

#Prints table of Top 10 counties for current date
US_top_ten_county_table= return_top_table(df=US_df, table_date=US_data[2], dataset_type=dataset_type, kind='US', one_date=True)
st.table(US_top_ten_county_table)

#Get a dataframe of top ten counties by date, with reorganized date column, 5 digit FIPS codes, and dates in datetime format
US_top_ten_dates_df=get_top_ten_counties_by_date(county_df, all_dates[-1])
US_top_ten_dates_df=reorg_date_df(US_top_ten_dates_df)
US_top_ten_dates_df=convert_FIPS(df=US_top_ten_dates_df)
US_top_ten_dates_df=format_date(US_top_ten_dates_df)

#Plotting Top 10 counties over time using plotly express
st.plotly_chart(plot_top_count_vs_time(US_top_ten_dates_df, dataset_type))

#Plot subplots of all US cases, Top 10 states, and Top 10 counties (for current) date vs time
st.plotly_chart(plot_top_US_county_state(records_df, dates, dataset_type))
    

####################
#Individual State County Data
st.subheader('Explore Data: Individual State Counties')

#Choose individual state to see county-level data
unique_states=list(records_df['State'].unique())
selected_state=st.selectbox('Choose a state to view county data', unique_states, index=32, key='states') #user selected state

#Plot state data on heatmap using select_map_type function
state_data=select_map_type(records_df=records_df, dates=dates, dataset_type=dataset_type, counties=counties, kind=selected_state)
state_figure=state_data[0]
state_df=state_data[1]
st.plotly_chart(state_figure)

#Prints number of cases & a table of Top 10 counties for current date 
state_top_ten_county_table= return_top_table(df=state_df, table_date=state_data[2], dataset_type=dataset_type, kind=selected_state, one_date=True)
#Return statement with today's total case count
st.write(get_daily_count(df=state_df, dataset_type=dataset_type, count_col='Count', date_col='Date', return_date=None))
st.table(state_top_ten_county_table)


#Get a dataframe of top ten counties by date, with reorganized date column, 5 digit FIPS codes, and dates in datetime format
state_top_ten_dates_df=get_top_ten_counties_by_date(county_df, all_dates[-1], state=selected_state)
state_top_ten_dates_df=reorg_date_df(state_top_ten_dates_df)
state_top_ten_dates_df=convert_FIPS(df=state_top_ten_dates_df)
state_top_ten_dates_df=format_date(state_top_ten_dates_df)

#Plotting Top 10 counties in state over time using plotly express
st.plotly_chart(plot_top_count_vs_time(state_top_ten_dates_df, dataset_type, kind=selected_state))

#Option to plot any county within state over time using plotly express
st.write('Select counties to compare (default is Top 5 counties)')
top_five_state_names=list(state_top_ten_county_table['County, State'].unique())[:5]
st.plotly_chart(plot_counties_vs_time(records_df, dataset_type, default=top_five_state_names, kind=selected_state))







