"""
Load pamap2_quality_clean.csv into a SQLite database, using the schema
in pamap2_schema.sql. Run this after pamap2_analysis_scipy.py has produced
the CSV.
"""

import sqlite3
import pandas as pd

# read the CSV your analysis script produced
quality_df = pd.read_csv("pamap2_quality_clean.csv")

# subjects table needs just one row per subject (not one row per reading)
subjects_df = quality_df[
    ["subject_id", "gender", "age", "height_cm", "weight_kg",
     "resting_hr", "max_hr", "dominant_hand", "bmi"]
].drop_duplicates(subset="subject_id")

# connect to (or create) the database file
conn = sqlite3.connect("pamap2.db")

# run the schema file to create tables/views
with open("pamap2_schema.sql") as f:
    conn.executescript(f.read())

# load the data into the tables
quality_df.to_sql("readings_raw", conn, if_exists="replace", index=False)
subjects_df.to_sql("subjects", conn, if_exists="replace", index=False)
conn.commit()

# quick sanity check -- print the first few rows of the summary view
check = pd.read_sql("SELECT * FROM signal_quality_summary LIMIT 10", conn)
print(check)

conn.close()
print("\nSaved pamap2.db -- ready to connect Tableau to it.")