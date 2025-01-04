# Install required libraries
# pip install sentence-transformers sqlalchemy python-dotenv psycopg2-binary

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Table, Column, Integer, Text, MetaData, select, func
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer
import numpy as np

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URI = os.getenv("DATABASE_URI")
if not DATABASE_URI:
    raise ValueError("DATABASE_URI not set in .env file")

# Initialize SQLAlchemy engine and session
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

# Define the metadata and questions table
metadata = MetaData()

questions_table = Table(
    "questions",
    metadata,
    Column("question_id", Integer, primary_key=True),
    Column("chapter_no", Integer),
    Column("verse_no", Integer),
    Column("possible_question", Text),
    Column("question_embedding", Text)  # Using Text for JSON-like storage
)

# Load the Sentence Transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')  # Generates 384-dimensional embeddings

def query_to_embedding(query: str) -> str:
    """
    Converts a user query into a vector embedding.

    Args:
        query (str): The user's query.

    Returns:
        str: A string representation of the embedding vector.
    """
    embedding = model.encode(query)  # Generate embedding
    return "[" + ",".join(map(str, embedding)) + "]"  # Convert to PostgreSQL-compatible string

def search_similar_questions(query_embedding: str, limit: int = 5):
    """
    Searches for the most similar questions in the database using cosine similarity.

    Args:
        query_embedding (str): The embedding of the user's query as a string.
        limit (int): The number of results to return.

    Returns:
        List[Tuple[int, int, float]]: A list of tuples containing chapter_no, verse_no, and similarity score.
    """
    # Use SQLAlchemy to query the database
    query = select(
        questions_table.c.chapter_no,
        questions_table.c.verse_no,
        (questions_table.c.question_embedding.op('<=>')(query_embedding)).label("distance")
    ).order_by(
        questions_table.c.question_embedding.op('<=>')(query_embedding)
    ).limit(limit)

    # Execute the query
    results = session.execute(query).fetchall()
    return results

def main():
    # Take user input
    user_query = input("Enter your question: ")

    # Convert the query to an embedding
    query_embedding = query_to_embedding(user_query)
    print(f"Query embedding: {query_embedding}")

    # Search for similar questions in the database
    results = search_similar_questions(query_embedding)

    # Display the results
    if results:
        print("\nMost relevant results:")
        for chapter_no, verse_no, distance in results:
            print(f"Chapter {chapter_no}, Verse {verse_no} (Distance: {distance:.4f})")
    else:
        print("No results found.")

if __name__ == "__main__":
    main()