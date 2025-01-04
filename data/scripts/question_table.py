import pandas as pd
import ast
from sentence_transformers import SentenceTransformer

# Load the SentenceTransformer model for 384-dimensional embeddings
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Input and output file paths
input_file = 'data/Bhagwad_Gita_Verses_English_Questions.csv'
output_file = 'data/processed/questions.csv'

# Load the input CSV
print("Loading input file...")
data = pd.read_csv(input_file)

# Rename columns to match the desired schema
data.rename(columns={'chapter': 'chapter_no', 'verse': 'verse_no'}, inplace=True)

# Select relevant columns
questions_df = data[['chapter_no', 'verse_no', 'question']]

# Drop rows with missing questions
questions_df.dropna(subset=['question'], inplace=True)

# Generate question embeddings
print("Generating question embeddings...")
questions_df['question_embedding'] = questions_df['question'].apply(lambda x: model.encode(x).tolist())

# Save to CSV
print(f"Saving to {output_file}...")
questions_df.to_csv(output_file, index=False)

print("Process completed. Output saved to:", output_file)
