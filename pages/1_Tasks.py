import datetime
import sqlite3
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from collections import defaultdict
import glob 
from pathlib import Path
import os

from utils.useful_functions import connect_db, initialize_data, load_data, STATUSES, PRIORITIES

def update_data(conn, df):
    df.to_sql(name='tasks', con=conn, if_exists='replace', index=False)
    st.toast("Database updated!")
    st.session_state.has_uncommitted_changes = False

def lock():
    st.session_state.lock = True

def validated_submission():
    task_id = int(max(st.session_state.df['id']) + 1)
    #task_id = int(max(df['id']) + st.session_state.attempt)
    issue = st.text_area("Describe the task", disabled=st.session_state.lock, key=f"issue_{st.session_state.attempt}")
    subsystem = st.selectbox("Sub-system", subsystems, disabled=st.session_state.lock, key=f"subsystem_{st.session_state.attempt}")
    task_status = st.pills("Status", ["Not started", "In Progress"], disabled=st.session_state.lock, key=f"status_{st.session_state.attempt}")
    priority = st.pills("Priority", ["High", "Medium", "Low"], disabled=st.session_state.lock, key=f"priority_{st.session_state.attempt}")
    duration = st.number_input("Task expected duration (in days)", disabled=st.session_state.lock, key=f"duration_{st.session_state.attempt}")
    contact = st.text_input("Contact person", disabled=st.session_state.lock, key=f"contact_{st.session_state.attempt}")

    submit = st.button("Submit", on_click=lock)
    if "status" in st.session_state:
        st.error(st.session_state.status)
    if submit:
        # Check that all fields are filled
        if None in [issue, subsystem, task_status, priority, duration, contact]:
            st.session_state.status = "Please fill in all fields."
            st.session_state.lock = False
            st.rerun()
        # Accept the submission
        else:
            st.session_state.task_id = task_id
            st.session_state.issue = issue
            st.session_state.subsystem = subsystem
            st.session_state.task_status = task_status
            st.session_state.priority = priority
            st.session_state.duration = duration
            st.session_state.contact = contact
            st.session_state.lock = False
            if "status" in st.session_state:
                del st.session_state.status
            st.session_state.attempt += 1
            st.rerun()
            
def delete_submission():
    del st.session_state.task_id
    del st.session_state.issue
    del st.session_state.subsystem
    del st.session_state.task_status
    del st.session_state.priority
    del st.session_state.duration
    del st.session_state.contact

@st.fragment
def fill_in_form():

    validated_submission()
    if "task_status" in st.session_state:
        # Make a dataframe for the new task and append it to the dataframe in session
        # state.
        today = datetime.datetime.now().strftime("%d-%m-%Y")
        df_new = pd.DataFrame(
            [
                {   
                    "id": st.session_state.task_id,
                    "description": st.session_state.issue,
                    "sub_system": st.session_state.subsystem,
                    "status": st.session_state.task_status,
                    "priority": st.session_state.priority,
                    "submission_date": today,
                    "duration": st.session_state.duration,
                    "contact_person": st.session_state.contact,
                }
            ]
        )
        # Show a little success message.
        st.toast("Task submitted!")
        #st.dataframe(df_new, use_container_width=True, hide_index=True)
        # Convert the date column to date format
        df_new["submission_date"] = pd.to_datetime(df_new["submission_date"], dayfirst=True)
        delete_submission()

        return df_new

# -----------------------------------------------------------------------------
# Show app title and description.
st.set_page_config(page_title="Tasks", page_icon=":card_file_box:")
st.title(":card_file_box: Tasks")
st.info(
    """
    Use the table below to add, remove, and edit items.
    And don't forget to commit your changes when you're done.
    """
)

# Connect to database and create table if needed
conn, db_was_just_created = connect_db()

# Initialize data.
if db_was_just_created:
    initialize_data(conn)
    st.toast("Database initialized with some sample data.")

# Load data from database
df = load_data(conn)
df['submission_date'] = pd.to_datetime(df["submission_date"])
if "df" not in st.session_state:
    st.session_state.df = df

# Initialization
last_id = max(df['id'])

# Show a section to add a new task.
st.header("Add a task")

# We're adding tickets via an `st.form` and some input widgets. If widgets are used
# in a form, the app will only rerun once the submit button is pressed.
subsystems = ["HV", "LV", "DAQ/monitoring", "Time reference", "MCP", "Electronics", "Cooling", "Trigger", "Beamline", "Mechanics/Prototype", "Planning"]

if "attempt" not in st.session_state:
    st.session_state.attempt = 1
if "lock" not in st.session_state:
    st.session_state.lock = False

new_row = fill_in_form()
st.session_state.df = pd.concat([new_row, st.session_state.df], axis=0, ignore_index=True)

# Show section to view and edit existing tickets in a table.
st.header("Existing tasks")
st.write(f"Number of tasks: `{len(st.session_state.df)}`")

# Show the tickets dataframe with `st.data_editor`. This lets the user edit the table
# cells. The edited data is returned as a new dataframe.
edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",  # Allow appending/deleting rows.
    column_config={
        "id" : "Task ID",
        "description" : "Description",
        "sub_system" : "Sub-system",
        "status": st.column_config.SelectboxColumn(
            "Status",
            help="Task status",
            options=STATUSES,
            required=True,
        ),
        "priority": st.column_config.SelectboxColumn(
            "Priority",
            help="Priority",
            options=PRIORITIES,
            required=True,
        ),
        "submission_date" : st.column_config.DateColumn(
            "Submisison Date",
            format="DD.MM.YYYY",
        ),
        "duration" : "Duration",
        "contact_person" : "Contact Person",
    },
    # Disable editing the ID and Date Submitted columns.
    disabled=["id", "submission_date", "sub_system"],
    key="tasks_table",
)

elements_were_added = bool(len(st.session_state.df) > len(df))
table_was_edited = any(len(v) for v in st.session_state.tasks_table.values())
st.session_state.has_uncommitted_changes = elements_were_added or table_was_edited

added_rows = st.session_state.df[st.session_state.df['id'] > last_id].reset_index()

st.button(
    "Commit changes",
    type="primary",
    disabled=not st.session_state.has_uncommitted_changes,
    # Update data in database
    on_click=update_data,
    args=(conn, edited_df),
)