import os
import csv
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List

# Load the Sentence Transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')  # Model with 768-dimensional embeddings

# Function to generate embeddings for a list of texts
def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generates embeddings for a list of texts using Sentence Transformers.

    Args:
        texts (List[str]): List of input texts.

    Returns:
        List[List[float]]: List of embeddings (each embedding is a list of floats).
    """
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()

# Function to Process CSV and Add Embeddings
def process_csv(input_file: str, output_file: str):
    """
    Function to process a CSV file, generate embeddings for 'translation' and 'commentary' columns,
    and save the updated data to a new CSV file.

    Args:
        input_file (str): Path to the input CSV file.
        output_file (str): Path to the output CSV file.
    """
    with open(input_file, mode='r', encoding='utf-8') as infile, \
         open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["translation_embedding", "commentary_embedding"]  # Add new columns
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        # Read all rows into a list
        rows = list(reader)
        
        # Extract 'translation' and 'commentary' texts
        translations = [row["translation"] for row in rows]
        commentaries = [row["commentary"] for row in rows]
        
        # Generate embeddings for translations and commentaries
        print("Generating embeddings for translations...")
        translation_embeddings = generate_embeddings(translations)
        
        print("Generating embeddings for commentaries...")
        commentary_embeddings = generate_embeddings(commentaries)
        
        # Add embeddings to the corresponding rows
        for row, trans_embed, comm_embed in zip(rows, translation_embeddings, commentary_embeddings):
            row["translation_embedding"] = str(trans_embed)  # Store as string
            row["commentary_embedding"] = str(comm_embed)    # Store as string
            writer.writerow(row)

if __name__ == "__main__":
    # Input and output file paths
    input_csv = "data/processed/temp.csv"  # Replace with your actual input file
    output_csv = "data/processed/temp_with_embeddings.csv"  # Replace with your desired output file

    # Check if input file exists
    if not os.path.exists(input_csv):
        print(f"Error: The file '{input_csv}' does not exist.")
    else:
        print("Generating embeddings...")
        process_csv(input_csv, output_csv)
        print(f"Embeddings successfully added and saved to '{output_csv}'")