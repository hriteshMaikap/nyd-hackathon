import pandas as pd
import os

# Load CSV data into pandas DataFrame
df = pd.read_csv("data\\Bhagwad_Gita_Verses_English_Questions.csv")

# Mapping Sanskrit to English speakers
sanskrit_to_english = {
    "भगवान": "Lord Krishna",
    "धृतराष्ट्र": 'Dhritarashtra',
    "सञ्जय": 'Sanjay',
    "अर्जुन": 'Arjun',
    "संजय": "Sanjay"
}

# Step 1: Replace Sanskrit speakers with English equivalents in place
df['speaker'].replace(sanskrit_to_english, inplace=True)

# Step 2: Select the required columns (chapter, verse, speaker (updated), sanskrit, translation)
df_processed = df[['chapter', 'verse', 'speaker', 'sanskrit', 'translation']]

# Step 3: Ensure the directory exists for saving the processed file
os.makedirs('data/processed', exist_ok=True)

# Step 4: Save the processed DataFrame to a new file
output_file = 'data/processed/info.csv'
df_processed.to_csv(output_file, index=False)

print(f"Processed data has been saved to {output_file}.")
