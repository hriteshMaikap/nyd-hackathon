import pandas as pd
from sqlalchemy import create_engine, Table, Column, Integer, Text, MetaData, Float
from sqlalchemy.dialects.postgresql import ARRAY
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Reflect the table schema (if the table already exists)
metadata.reflect(bind=engine)
if 'pys_question' in metadata.tables:
    pys_question = metadata.tables['pys_question']
else:
    # Define the table schema if it doesn't exist
    pys_question = Table('pys_question', metadata,
                         Column('question_id', Integer, primary_key=True),
                         Column('chapter_no', Integer, nullable=False),
                         Column('verse_no', Integer, nullable=False),
                         Column('sanskrit', Text),
                         Column('translation', Text),
                         Column('possible_question', Text),
                         Column('question_embedding', ARRAY(Float))  # Use ARRAY for vector type
                        )
    metadata.create_all(engine)  # Create the table if it doesn't exist

# Load the input CSV file
input_file = 'data/processed/pys_questions.csv'
print("Loading input file...")
questions_df = pd.read_csv(input_file)

# Check if required columns exist
required_columns = ['chapter_no', 'verse_no', 'sanskrit', 'translation', 'possible_question', 'question_embedding']
for col in required_columns:
    if col not in questions_df.columns:
        raise ValueError(f"Column '{col}' is missing from the input file.")

# Convert 'question_embedding' from string representation of list to actual list
questions_df['question_embedding'] = questions_df['question_embedding'].apply(lambda x: eval(x) if isinstance(x, str) else x)

# Insert data into the PostgreSQL table
try:
    with engine.connect() as connection:
        # Use pandas' to_sql for bulk insertion
        questions_df.to_sql('pys_question', con=connection, if_exists='append', index=False)
    print("Data insertion complete!")
except Exception as e:
    print(f"An error occurred during data insertion: {e}")