import pandas as pd
from sentence_transformers import SentenceTransformer

# Load the SentenceTransformer model for 384-dimensional embeddings
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Input and output file paths
input_file = 'data/Patanjali_Yoga_Sutras_Verses_English_Questions.csv'
output_file = 'data/processed/patanjali_questions.csv'

# Load the input CSV
print("Loading input file...")
questions_df = pd.read_csv(input_file)

# Check if the 'question' column exists
if 'question' not in questions_df.columns:
    raise ValueError("The input file must contain a 'question' column.")

# Generate question embeddings
print("Generating question embeddings...")
questions_df['question_embedding'] = questions_df['question'].apply(lambda x: model.encode(x).tolist())

# Save the updated DataFrame to a new CSV file
print(f"Saving processed data to {output_file}...")
questions_df.to_csv(output_file, index=False)

print("Processing complete!")
