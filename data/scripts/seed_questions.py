import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv
import os
import ast

# Load environment variables
load_dotenv()
DATABASE_URI = os.getenv("DATABASE_URI")
if not DATABASE_URI:
    raise ValueError("DATABASE_URI not set in .env file")

# Connect to the database
engine = create_engine(DATABASE_URI)
metadata = MetaData()

# Define the questions table
questions_table = Table(
    "questions",
    metadata,
    Column("question_id", Integer, primary_key=True),
    Column("chapter_no", Integer),
    Column("verse_no", Integer),
    Column("possible_question", Text),
    Column("question_embedding", Text)  # Using Text for JSON-like storage
)

# Load the CSV file
def load_csv(file_path):
    df = pd.read_csv(file_path)
    df['question_embedding'] = df['question_embedding'].apply(ast.literal_eval)  # Convert string to list
    return df

# Seed the data into the database
def seed_questions_table(csv_file):
    df = load_csv(csv_file)
    with engine.begin() as connection:
        for _, row in df.iterrows():
            stmt = insert(questions_table).values(
                chapter_no=row['chapter_no'],
                verse_no=row['verse_no'],
                possible_question=row['question'],
                question_embedding=row['question_embedding']
            )
            connection.execute(stmt)

if __name__ == "__main__":
    # Path to your questions.csv
    csv_file_path = "data/processed/questions.csv"
    seed_questions_table(csv_file_path)
    print("Data seeded successfully!")
