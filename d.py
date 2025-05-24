import streamlit as st
import pandas as pd
import sqlalchemy
import plotly.express as px
import warnings
from datetime import datetime, time

warnings.filterwarnings('ignore')

# Database connection parameters
USER = 'root'
PASSWORD = 'your_password'
HOST = 'localhost'
DATABASE = 'students'
TABLE = 'cafteria'

# Create a connection using SQLAlchemy with pymysql
engine = sqlalchemy.create_engine(f'mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DATABASE}')

# Load data from the database table into a DataFrame
df = pd.read_sql_table(TABLE, con=engine)

st.set_page_config(page_title="EDA!!!", page_icon=":bar_chart:", layout="wide")

st.title(":bar_chart: AASTU Cafeteria EDA")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

col1, col2 = st.columns((2))

# Convert service_time to datetime
df['service_time'] = pd.to_datetime(df['service_time'], errors='coerce')

# Create weekday column
df['weekday'] = df['service_time'].dt.day_name()

# Define meal categories based on service time
def category(service_time):
    if time(7, 0) <= service_time.time() <= time(8, 30):
        return "breakfast"
    elif time(11, 30) <= service_time.time() <= time(13, 30):
        return "lunch"
    else:
        return "dinner"

# Apply category function to create meal column
df['meal'] = df['service_time'].apply(category)

# Getting the min and max date
startDate = df['service_time'].min()
endDate = df['service_time'].max()

# User input for date filtering
with col1:
    date1 = st.date_input("Start Date", startDate.date())

with col2:
    date2 = st.date_input("End Date", endDate.date())

# Filter the DataFrame based on selected dates
df_filtered = df[(df['service_time'] >= pd.to_datetime(date1)) & (df['service_time'] <= pd.to_datetime(date2))]

# Check if filtering worked
st.write(f"Filtered records: {df_filtered.shape[0]}")

st.sidebar.header("Choose your filter: ")

# Filter by student_id
student_id = st.sidebar.multiselect("Pick student_id", df_filtered["student_id"].unique())
if student_id:
    df_filtered = df_filtered[df_filtered["student_id"].isin(student_id)]

# Filter by meal type
meal = st.sidebar.multiselect("Pick the meal type", df_filtered["meal"].unique())
if meal:
    df_filtered = df_filtered[df_filtered["meal"].isin(meal)]

# Filter by weekday
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
selected_weekdays = st.sidebar.multiselect("Pick Weekdays", weekdays)

if selected_weekdays:
    df_filtered = df_filtered[df_filtered['weekday'].isin(selected_weekdays)]

# Grouping for visualization
category_df = df_filtered.groupby("meal", as_index=False)["student_id"].count()
category_df.rename(columns={"student_id": "total_students"}, inplace=True)

# Visualizations
with col1:
    st.subheader("Meal wise Service")
    fig = px.bar(category_df, x="meal", y="total_students", text=['{:,.2f}'.format(x) for x in category_df["total_students"]],
                 template="seaborn")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Gender-wise Distribution")
    gender_counts = df_filtered['sex'].value_counts().reset_index()
    gender_counts.columns = ['sex', 'total_students']

    fig = px.pie(gender_counts, values='total_students', names='sex', hole=0.5)
    fig.update_traces(textinfo='label+percent')
    st.plotly_chart(fig, use_container_width=True)

cl1, cl2 = st.columns((2))

with cl1:
    with st.expander("Category View Data"):
        st.write(category_df)
        csv = category_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Data", data=csv, file_name="Category.csv", mime="text/csv",
                           help='Click here to download the data as a CSV file')

with cl2:
    with st.expander("Gender View Data"):
        gender_data = gender_counts
        st.write(gender_data)
        csv = gender_data.to_csv(index=False).encode('utf-8')
        st.download_button("Download Data", data=csv, file_name="Gender.csv", mime="text/csv",
                           help='Click here to download the data as a CSV file')

# Time Series Analysis
df_filtered["month_year"] = df_filtered["service_time"].dt.to_period("M")
st.subheader('Time Series Analysis')

# Group by month and sum net_charge
linechart = df_filtered.groupby(df_filtered["month_year"].dt.strftime("%Y : %b"))["net_charge"].sum().reset_index()
linechart.rename(columns={"net_charge": "total_net_charge"}, inplace=True)

# Create the line chart
fig2 = px.line(linechart, x="month_year", y="total_net_charge", labels={"total_net_charge": "Total Net Charge"}, height=500, width=1000, template="gridon")
st.plotly_chart(fig2, use_container_width=True)

with st.expander("View Data of TimeSeries:"):
    st.write(linechart)
    csv = linechart.to_csv(index=False).encode("utf-8")
    st.download_button('Download Data', data=csv, file_name="TimeSeries.csv", mime='text/csv')