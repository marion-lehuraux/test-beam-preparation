import sqlite3
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from collections import defaultdict
import glob 
from pathlib import Path
import os

PRIORITIES = ['Low', 'Medium', 'High']
STATUSES = ['Not Started', 'In Progress', 'Done']

def connect_db():
    """Connects to the sqlite database."""

    DB_FILENAME = Path(__file__).parent.parent / "tasks_demo.db"
    db_already_exists = DB_FILENAME.exists()

    conn = sqlite3.connect(DB_FILENAME)
    db_was_just_created = not db_already_exists

    return conn, db_was_just_created

def initialize_data(conn):
    """Initializes the task database."""
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            sub_system TEXT,
            status TEXT,
            priority TEXT,
            submission_date DATETIME,
            duration INTEGER,
            contact_person TEXT
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO tasks
            (description, sub_system, status, priority, submission_date, duration, contact_person)
        VALUES
            ('This is a test task.', 'HV', 'Not Started', 'Low', '27-02-2025', 10, 'Marion'),
            ('This is an important test task.', 'HV', 'Not Started', 'High', '27-02-2025', 20, 'Marion'),
            ('This is a another test task.', 'LV', 'Not Started', 'Medium', '27-02-2025', 10, 'Michal'),
            ('Have organisation meeting', 'Planning', 'In Progress', 'Low', '28-02-2025', 2, 'Marion')
        """
    )
    conn.commit()

def load_data(conn):
    """Loads the tasks data from the database."""
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM tasks")
        data = cursor.fetchall()
    except:
        return None

    df = pd.DataFrame(
        data,
        columns=[
            "id",
            "description",
            "sub_system",
            "status",
            "priority",
            "submission_date",
            "duration",
            "contact_person",
        ],
    )

    return df
