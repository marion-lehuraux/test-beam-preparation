import sqlite3
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from collections import defaultdict
import glob 
from pathlib import Path
import os
import datetime

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
            starting_date DATE,
            duration INTEGER,
            expected_end_date DATE,
            actual_end_date DATE,
            is_on_track BOOLEAN,
            last_edited DATETIME,
            priority TEXT,
            contact_person TEXT
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO tasks
            (description, sub_system, status, starting_date, duration, expected_end_date, actual_end_date, is_on_track, last_edited, priority, contact_person)
        VALUES
            ('Testing the database.', 'Planning', 'In Progress', '13-03-2025', 1, '14-03-2025', '14-03-2025', TRUE, '13-03-2025', 'Medium', 'Marion'),
            ('Testing the database again.', 'Planning', 'In Progress', '13-03-2025', 3, '16-03-2025', '14-03-2025', TRUE, '13-03-2025', 'High', 'Marion')
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
            "starting_date",
            "duration",
            "expected_end_date",
            "actual_end_date",
            "is_on_track",
            "last_edited",
            "priority",
            "contact_person"
        ],
    )

    df["starting_date"] = pd.to_datetime(df["starting_date"], dayfirst=True)
    df["expected_end_date"] = pd.to_datetime(df["expected_end_date"], dayfirst=True)
    df["actual_end_date"] = pd.to_datetime(df["actual_end_date"], dayfirst=True)
    df["last_edited"] = pd.to_datetime(df["last_edited"], dayfirst=True)
    df["is_on_track"] = df['is_on_track'].astype('bool')

    today = datetime.datetime.today()
    df.loc[(df['expected_end_date'] < today) & (df['status'] != 'Done'), 'is_on_track'] = False

    return df
