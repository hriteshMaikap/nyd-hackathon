import pandas as pd
from sqlalchemy import create_engine, Table, Column, Integer, Text, MetaData
from dotenv import load_dotenv
import os

load_dotenv()

# Database connection
DATABASE_URI = os.getenv("DATABASE_URI")
if not DATABASE_URI:
    raise ValueError("DATABASE_URI not set in .env file")

engine = create_engine(DATABASE_URI)
metadata = MetaData()

# Define the chapter table
chapter_table = Table(
    "chapter",
    metadata,
    Column("chapter_no", Integer, primary_key=True),
    Column("chapter_heading", Text),
    Column("chapter_desc_heading", Text),
    Column("chapter_intro", Text)
)

# Load CSV data
df = pd.read_csv("data/scraped/chapters.csv")

# Rename columns to match the table schema
df.rename(columns={
    "chapter_title": "chapter_heading",
    "chapter_desc_heading": "chapter_desc_heading",
    "chapter_intro": "chapter_intro"
}, inplace=True)

# Insert data into the table
with engine.connect() as connection:
    # Begin a new transaction
    trans = connection.begin()
    try:
        for index, row in df.iterrows():
            # Print the row being processed
            print(f"Processing row {index}: {row.to_dict()}")

            insert_stmt = chapter_table.insert().values(
                chapter_no=row["chapter_no"],
                chapter_heading=row["chapter_heading"],
                chapter_desc_heading=row["chapter_desc_heading"],
                chapter_intro=row["chapter_intro"]
            )
            connection.execute(insert_stmt)

            # Debug: Print result of the insert
            print(f"Inserted row with chapter_no = {row['chapter_no']}")

        # Commit the transaction
        trans.commit()
        print("Chapter data seeding process completed.")
    except Exception as e:
        # Rollback the transaction in case of error
        trans.rollback()
        print(f"Error occurred: {e}")