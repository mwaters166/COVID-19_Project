# COVID-19 Tracking Project

## Michele Waters

![COVID-19 Tracking](https://raw.githubusercontent.com/mwaters166/COVID-19_Project/master/COVID-19_Tracking.png)


* This is a COVID-19 tracking project using data from Johns Hopkins (found here: https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data). You can explore confirmed cases, recovered cases, and mortality data of COVID-19 globally and in individual US states

* Link to COVID-19 global code: https://github.com/mwaters166/COVID-19_Project/blob/master/COVID19_app.py

* View video to see the walkthrough on streamlit:
https://raw.githubusercontent.com/mwaters166/COVID-19_Project/master/streamlit-COVID19_app-2020-03-23-23-03-06.webm.mp4?token=AIWDJKL2C2DUY7R6Z4XKP5K6QK5RM

* Written in Python & SQL; run in Streamlit: https://www.streamlit.io/

* To run the project (after downloading project folder and installing streamlit), navigate to the project folder within terminal and use the command: 
    streamlit run COVID19_app.py
    
* Update (3/26/2020): JHU is currently updating their data set, so the second part of this project (containing the US state data) will be updated once the state data has been returned/redirected to a new repository. The code was written based on formatting of archived JHU data sets, which originally contained US state data. The archived data can be found at the following link: https://github.com/CSSEGISandData/COVID-19/tree/master/archived_data/archived_time_series. -MW

* Update (3/27/2020): Updated project with US state data from "The Covid Tracking Project" api: https://covidtracking.com/api/
 The state data has the previous functionality, allows users the option to choose between: 'Positive tests', 'Negative tests', 'Total tests','Daily Change in Positive Cases','Daily Change in Negative Cases','Daily Change in Total Tests','Pending Tests','Hospitalized','Deaths', and 'Daily Change in Deaths' data. It also adds a feature displaying the top 10 states for chosen COVID-19 parameter.-MW
 
 * Link to COVID-19 state code (3/27/2020): https://github.com/mwaters166/COVID-19_Project/blob/master/States_COVID.py
 
 * View video to see the walkthrough of US state data on streamlit (3/27/2020):
 https://raw.githubusercontent.com/mwaters166/COVID-19_Project/master/streamlit-States_COVID-2020-03-27_video_walkthrough.mp4

 * Added Jupyter Notebooks (4/3/2020):
 
   -'States_Walkthrough_with_Prophet_ML'(https://github.com/mwaters166/COVID-19_Project/blob/master/States_Walkthrough_with_ProphetML.ipynb): explores the state data, then looks at using Prophet (https://facebook.github.io/prophet/) to forecast confirmed cases of COVID-19 in NY state. Data source: https://ourworldindata.org/covid-testing -MW
   
   -'International_Gov_COVID19_Measures'(https://github.com/mwaters166/COVID-19_Project/blob/master/International_Gov_COVID19_Measures.ipynb): compares positive cases, testing, and government measures implemented to limit COVID-19 spread in the US and South Korea. Data source: https://www.acaps.org/covid19-government-measures-dataset -MW
 


