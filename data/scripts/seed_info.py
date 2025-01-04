import pandas as pd
from sqlalchemy import create_engine, Table, Column, Integer, Text, MetaData, Float
from sqlalchemy.dialects.postgresql import ARRAY
from dotenv import load_dotenv
import os
import ast

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URI = os.getenv("DATABASE_URI")
if not DATABASE_URI:
    raise ValueError("DATABASE_URI not set in .env file")

engine = create_engine(DATABASE_URI)
metadata = MetaData()

# Define the info table
info_table = Table(
    "info",
    metadata,
    Column("chapter_no", Integer, primary_key=True, nullable=False),
    Column("verse_no", Integer, primary_key=True, nullable=False),
    Column("sanskrit_verse", Text),
    Column("speaker_name", Text),
    Column("english_translations", Text),
    Column("commentary", Text),
    Column("translation_embedding", ARRAY(Float)),
    Column("commentary_embedding", ARRAY(Float))
)

# Function to parse stringified embeddings back to arrays
def parse_embedding(embedding_str):
    try:
        # Convert the string representation of a list back to a Python list
        return list(ast.literal_eval(embedding_str))
    except (ValueError, SyntaxError):
        return None

# Load CSV data
data_path = "data/processed/temp_with_embeddings.csv"
df = pd.read_csv(data_path)

# Parse embeddings back to lists
df["translation_embedding"] = df["translation_embedding"].apply(parse_embedding)
df["commentary_embedding"] = df["commentary_embedding"].apply(parse_embedding)

# Rename columns to match the database schema
df.rename(
    columns={
        "chapter": "chapter_no",
        "verse": "verse_no",
        "sanskrit": "sanskrit_verse",
        "speaker": "speaker_name",
        "translation": "english_translations",
    },
    inplace=True
)

# Insert data into the database
try:
    with engine.begin() as connection:
        df.to_sql("info", connection, if_exists="append", index=False, method="multi")
    print("Data ingestion completed successfully.")
except Exception as e:
    print(f"Error during data ingestion: {e}")
