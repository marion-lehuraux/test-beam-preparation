import streamlit as st
import pandas as pd 
import glob 
import os

from utils.useful_functions import connect_db, initialize_data, load_data, PRIORITIES, STATUSES

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title="Home",
    page_icon=":hammer_and_wrench:",  # This is an emoji shortcode. Could be a URL too.
)


st.write("# 2025 TORCH Test beam preparation :clipboard:")

st.markdown(
    """
    Some description about what this is meant to do. 
    """
)

# Get data 
if "df" in st.session_state:
    df = st.session_state.df
else: 
    # Connect to database and create table if needed
    conn, db_was_just_created = connect_db()

    # Initialize data.
    if db_was_just_created:
        initialize_data(conn)
        st.toast("Database initialized with some sample data.")

    # Load data from database
    df = load_data(conn)

# At glance 
st.write("## A glance at the high priority tasks ")

st.dataframe(df[df['priority']=='High'])

st.write("## Browse tasks ")
# Read selection from user 
min_value_duration = df['duration'].min()
max_value_duration = df['duration'].max()

from_dur, to_dur = st.slider(
    'Task duration',
    min_value=min_value_duration,
    max_value=max_value_duration+1,
    value=[min_value_duration, max_value_duration])

contacts = df['contact_person'].unique()
if not len(contacts):
    st.warning("Select at least one contact person.")
selected_persons = st.multiselect(
    'Select based on contact persons',
    contacts,
    default=contacts,
    )

subsystems = df['sub_system'].unique()
if not len(subsystems):
    st.warning("Select at least one sub-system.")
selected_systems = st.multiselect(
    'Select based on sub-system',
    subsystems,
    default=subsystems,
    )

selected_priorities = st.multiselect(
    'Select based on priority',
    PRIORITIES,
    default=PRIORITIES,
    )

selected_status = st.multiselect(
    'Select based on status',
    STATUSES,
    default=STATUSES,
    )

# Filter the data
filtered_df = df[
    (df['contact_person'].isin(selected_persons))
    & (df['priority'].isin(selected_priorities))
    & (df['sub_system'].isin(selected_systems))
    & (df['duration'] <= to_dur)
    & (from_dur <= df['duration'])
]

st.dataframe(filtered_df)