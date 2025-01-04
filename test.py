# Install required libraries
# pip install sentence-transformers sqlalchemy python-dotenv psycopg2-binary pandas numpy

import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, Table, Column, Integer, Text, MetaData, select, func
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer

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

def evaluate_accuracy(test_results_df):
    """
    Calculate accuracy metrics for the test results.
    
    Args:
        test_results_df (pd.DataFrame): DataFrame containing test results
        
    Returns:
        dict: Dictionary containing various accuracy metrics
    """
    # Calculate exact matches (both chapter and verse correct)
    exact_matches = (
        (test_results_df['predicted_chapter'] == test_results_df['actual_chapter']) & 
        (test_results_df['predicted_verse'] == test_results_df['actual_verse'])
    ).mean()
    
    # Calculate chapter-only accuracy
    chapter_accuracy = (
        test_results_df['predicted_chapter'] == test_results_df['actual_chapter']
    ).mean()
    
    # Calculate verse-only accuracy (within correct chapters)
    verse_accuracy = (
        (test_results_df['predicted_chapter'] == test_results_df['actual_chapter']) & 
        (test_results_df['predicted_verse'] == test_results_df['actual_verse'])
    ).sum() / (test_results_df['predicted_chapter'] == test_results_df['actual_chapter']).sum()
    
    return {
        'exact_match_accuracy': exact_matches,
        'chapter_accuracy': chapter_accuracy,
        'verse_accuracy': verse_accuracy
    }

def main():
    # Read the test file
    test_df = pd.read_csv('test_file.csv')
    
    # Initialize results list
    results = []
    
    # Process each question
    for idx, row in test_df.iterrows():
        # Convert query to embedding
        query_embedding = query_to_embedding(row['question'])
        
        # Search for similar questions
        search_results = search_similar_questions(query_embedding, limit=1)
        
        if search_results:
            pred_chapter, pred_verse, distance = search_results[0]
            
            # Store results
            results.append({
                'question': row['question'],
                'actual_chapter': row['chapter'],
                'actual_verse': row['verse'],
                'predicted_chapter': pred_chapter,
                'predicted_verse': pred_verse,
                'cosine_distance': distance
            })
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    # Save results to CSV
    results_df.to_csv('results.csv', index=False)
    
    # Calculate accuracy metrics
    accuracy_metrics = evaluate_accuracy(results_df)
    
    # Print accuracy metrics
    print("\nAccuracy Metrics:")
    print(f"Exact Match Accuracy: {accuracy_metrics['exact_match_accuracy']:.2%}")
    print(f"Chapter-only Accuracy: {accuracy_metrics['chapter_accuracy']:.2%}")
    print(f"Verse Accuracy (within correct chapters): {accuracy_metrics['verse_accuracy']:.2%}")
    
    # Print some example predictions
    print("\nSample Predictions (first 5):")
    print(results_df[['question', 'actual_chapter', 'actual_verse', 
                     'predicted_chapter', 'predicted_verse', 'cosine_distance']].head())

if __name__ == "__main__":
    main()