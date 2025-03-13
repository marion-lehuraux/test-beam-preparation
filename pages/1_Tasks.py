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
    st.session_state.elements_were_added = False
    st.session_state.table_was_edited = False

def data_changed(edited_df):
    # Update last edited column
    state = st.session_state["editor"]
    for row in state['edited_rows'].keys():
        change = state['edited_rows'][row]
        edited_df.loc[row, "last_edited"] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        if "starting_date" in change.keys() or "duration" in change.keys():
            edited_df.loc[row, "expected_end_date"] = edited_df.loc[row, "starting_date"] + datetime.timedelta(days=int(edited_df.loc[row, "duration"]))
        if "status" in change.keys():
            edited_df.loc[row, "is_on_track"] = False if datetime.datetime.today() > edited_df.loc[row, "expected_end_date"] and edited_df.loc[row, "status"] != 'Done' else True
    st.session_state.df = edited_df
    st.rerun()

def lock():
    st.session_state.lock = True

def validated_submission():
    task_id = int(max(st.session_state.df['id']) + 1)
    #task_id = int(max(df['id']) + st.session_state.attempt)
    issue = st.text_area("Describe the task", disabled=st.session_state.lock, key=f"issue_{st.session_state.attempt}")
    subsystem = st.selectbox("Sub-system", subsystems, disabled=st.session_state.lock, key=f"subsystem_{st.session_state.attempt}")
    task_status = st.pills("Status", ["Not started", "In Progress"], disabled=st.session_state.lock, key=f"status_{st.session_state.attempt}")
    starting_date = st.date_input("Starting date", datetime.date.today(), disabled=st.session_state.lock, key=f"starting_date_{st.session_state.attempt}")
    duration = st.number_input("Task expected duration (in days)", step=1, disabled=st.session_state.lock, key=f"duration_{st.session_state.attempt}")
    priority = st.pills("Priority", ["High", "Medium", "Low"], disabled=st.session_state.lock, key=f"priority_{st.session_state.attempt}")
    contact = st.text_input("Contact person", disabled=st.session_state.lock, key=f"contact_{st.session_state.attempt}")

    submit = st.button("Submit", on_click=lock)
    if "status" in st.session_state:
        st.error(st.session_state.status)
    if submit:
        # Check that all fields are filled
        if None in [issue, subsystem, task_status, starting_date, duration, priority, contact]:
            st.session_state.status = "Please fill in all fields."
            st.session_state.lock = False
            st.rerun()
        # Accept the submission
        else:
            st.session_state.task_id = task_id
            st.session_state.issue = issue
            st.session_state.subsystem = subsystem
            st.session_state.task_status = task_status
            st.session_state.starting_date = starting_date
            st.session_state.duration = duration
            st.session_state.priority = priority
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
    del st.session_state.starting_date
    del st.session_state.priority
    del st.session_state.duration
    del st.session_state.contact

@st.fragment
def fill_in_form():

    validated_submission()
    if "task_status" in st.session_state:
        # Make a dataframe for the new task and append it to the dataframe in session
        # state.
        today = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        expected_end_date = st.session_state.starting_date + datetime.timedelta(days=st.session_state.duration)
        df_new = pd.DataFrame(
            [
                {   
                    "id": st.session_state.task_id,
                    "description": st.session_state.issue,
                    "sub_system": st.session_state.subsystem,
                    "status": st.session_state.task_status,
                    "starting_date": st.session_state.starting_date,
                    "duration": st.session_state.duration,
                    "expected_end_date": expected_end_date,
                    "actual_end_date": '00-00-0000', 
                    "is_on_track": False if today > expected_end_date and st.session_state.task_status != 'Done' else True,
                    "last_edited": today,
                    "priority": st.session_state.priority,
                    "contact_person": st.session_state.contact,
                }
            ]
        )
        # Show a little success message.
        st.toast("Task submitted!")
        #st.dataframe(df_new, use_container_width=True, hide_index=True)
        # Convert the date column to date format
        df_new["starting_date"] = pd.to_datetime(df_new["starting_date"], dayfirst=True)
        df_new["expected_end_date"] = pd.to_datetime(df_new["expected_end_date"], dayfirst=True)
        df_new["actual_end_date"] = pd.to_datetime(df_new["actual_end_date"], dayfirst=True)
        df_new["last_edited"] = pd.to_datetime(df_new["last_edited"], dayfirst=True)

        delete_submission()

        return df_new


@st.fragment
def edit_table():
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
            "starting_date" : st.column_config.DateColumn(
                "Starting Date",
                format="DD.MM.YYYY",
            ),
            "duration" : "Duration (in days)",
            "expected_end_date" : st.column_config.DateColumn(
                "Expected End Date",
                format="DD.MM.YYYY",
            ),
            "actual_end_date" : st.column_config.DateColumn(
                "Actual End Date",
                format="DD.MM.YYYY",
            ),
            "is_on_track" : "Is On Track",
            "last_edited" : st.column_config.DateColumn(
                "Last Edited",
                format="DD.MM.YYYY-H.M.S",
            ),
            "priority": st.column_config.SelectboxColumn(
                "Priority",
                help="Priority",
                options=PRIORITIES,
                required=True,
            ),
            "contact_person" : "Contact Person",
        },
        # Disable editing the ID and Date Submitted columns.
        disabled=["id","expected_end_date", "sub_system", "is_on_track"],
        key="editor",
    )

    table_was_edited = any(len(v) for v in st.session_state.editor.values())

    if table_was_edited:   
        # Update automatically dependent columns
        data_changed(edited_df)


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
if "elements_were_added" not in st.session_state:
    st.session_state.elements_were_added = False
if "table_was_edited" not in st.session_state:
    st.session_state.table_was_edited = False
if "has_not_committed_changes" not in st.session_state:
    st.session_state.has_not_committed_changes = False

new_row = fill_in_form()
st.session_state.df = pd.concat([new_row, st.session_state.df], axis=0, ignore_index=True)

# Show section to view and edit existing tickets in a table.
st.header("Existing tasks")
st.write(f"Number of tasks: `{len(st.session_state.df)}`")

st.session_state.elements_were_added = bool(len(st.session_state.df) > len(df))

edit_table()

st.session_state.has_not_committed_changes = st.session_state.elements_were_added or st.session_state.table_was_edited

st.button(
    "Commit changes",
    type="primary",
    #disabled=not st.session_state.has_not_committed_changes,
    # Update data in database
    on_click=update_data,
    args=(conn, st.session_state.df),
)