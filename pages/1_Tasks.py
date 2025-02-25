import datetime
import random

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# Show app title and description.
st.set_page_config(page_title="Tasks", page_icon=":card_file_box:")
st.title(":card_file_box: Tasks")
st.write(
    """
    The tasks to be done are listed here with their status. 
    The user can create a new task, edit existing tasks, and view some statistics.
    """
)

# Load existing tasks

# Create a random Pandas dataframe with existing tickets.
if "df" not in st.session_state:

    df = pd.read_csv('dtb/tasks.csv', index_col=False)

    # Save the dataframe in session state (a dictionary-like object that persists across
    # page runs). This ensures our data is persisted when the app updates.
    st.session_state.df = df


# Show a section to add a new task.
st.header("Add a task")

# We're adding tickets via an `st.form` and some input widgets. If widgets are used
# in a form, the app will only rerun once the submit button is pressed.
subsystems = ["HV", "LV", "DAQ/monitoring", "Time reference", "MCP", "Electronics", "Cooling", "Trigger", "Beamline", "Mechanics/Prototype", "Planning"]
with st.form("add_task_form"):
    issue = st.text_area("Describe the task")
    subsystem = st.selectbox("Sub-system", subsystems)
    status = st.selectbox("Status", ["Not started", "In Progress"])
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    submitted = st.form_submit_button("Submit")

if submitted:
    # Make a dataframe for the new task and append it to the dataframe in session
    # state.
    recent_task_number = int(max(st.session_state.df.ID).split("-")[1])
    today = datetime.datetime.now().strftime("%m-%d-%Y")
    df_new = pd.DataFrame(
        [
            {
                "ID": f"TASK-{recent_task_number+1}",
                "Description": issue,
                "Sub-system": subsystem,
                "Status": status,
                "Priority": priority,
                "Date Submitted": today,
            }
        ]
    )

    # Show a little success message.
    st.write("Task submitted! Here are the task details:")
    st.dataframe(df_new, use_container_width=True, hide_index=True)
    st.session_state.df = pd.concat([df_new, st.session_state.df], axis=0)

# Show section to view and edit existing tickets in a table.
st.header("Existing tasks")
st.write(f"Number of tasks: `{len(st.session_state.df)}`")

# Show the tickets dataframe with `st.data_editor`. This lets the user edit the table
# cells. The edited data is returned as a new dataframe.
edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status",
            help="Task status",
            options=["Not started", "In Progress", "Closed"],
            required=True,
        ),
        "Priority": st.column_config.SelectboxColumn(
            "Priority",
            help="Priority",
            options=["High", "Medium", "Low"],
            required=True,
        ),
    },
    # Disable editing the ID and Date Submitted columns.
    disabled=["ID", "Date Submitted", "Sub-system"],
)

# Save updated status of database to csv 
edited_df.to_csv(f'dtb/tasks-{datetime.datetime.now().strftime("%Y%m%d-%H%M")}.csv', index=False)

# Show some metrics and charts about the ticket.
st.header("Statistics")

# Show metrics side by side using `st.columns` and `st.metric`.
col1, col2, col3 = st.columns(3)
num_open_tickets = len(st.session_state.df[st.session_state.df.Status == "Open"])
col1.metric(label="Number of open tickets", value=num_open_tickets, delta=10)
col2.metric(label="First response time (hours)", value=5.2, delta=-1.5)
col3.metric(label="Average resolution time (hours)", value=16, delta=2)

# Show two Altair charts using `st.altair_chart`.
st.write("")
st.write("##### Task status per month")
status_plot = (
    alt.Chart(edited_df)
    .mark_bar()
    .encode(
        x="month(Date Submitted):O",
        y="count():Q",
        xOffset="Status:N",
        color="Status:N",
    )
    .configure_legend(
        orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    )
)
st.altair_chart(status_plot, use_container_width=True, theme="streamlit")

st.write("##### Current task priorities")
priority_plot = (
    alt.Chart(edited_df)
    .mark_arc()
    .encode(theta="count():Q", color="Priority:N")
    .properties(height=300)
    .configure_legend(
        orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    )
)
st.altair_chart(priority_plot, use_container_width=True, theme="streamlit")