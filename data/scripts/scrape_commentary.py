import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Base URL
base_url = "https://www.holy-bhagavad-gita.org/"

# Function to fetch a URL with retries
def fetch_with_retries(url, retries=3, timeout=10):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response
        except Exception as e:
            print(f"Attempt {i + 1} failed for {url}: {e}")
            time.sleep(2)  # Wait before retrying
    raise Exception(f"Failed to fetch {url} after {retries} retries")

# Function to extract verse links from a chapter page
def extract_verse_links(chapter_url):
    try:
        response = fetch_with_retries(chapter_url)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find all verse links
        verse_links = []
        verse_spans = soup.find_all("span", class_="verseSmall")
        for span in verse_spans:
            link = span.find("a")["href"]
            verse_links.append(link)  # Store relative links (e.g., /chapter/1/verse/1)
        
        return verse_links
    except Exception as e:
        print(f"Error extracting verse links from {chapter_url}: {e}")
        return []

# Function to extract commentary from a verse page
def extract_commentary(verse_url):
    try:
        response = fetch_with_retries(verse_url)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find the commentary section
        commentary_div = soup.find("div", id="commentary")
        if commentary_div:
            # Extract all <p> tags inside the commentary section
            commentary = " ".join(p.text.strip() for p in commentary_div.find_all("p"))
        else:
            commentary = ""
        
        return commentary
    except Exception as e:
        print(f"Error extracting commentary from {verse_url}: {e}")
        return ""

# Function to process all chapters and verses
def process_verses():
    # Load existing info.csv (if any)
    try:
        df = pd.read_csv("data/processed/info.csv")
    except FileNotFoundError:
        df = pd.DataFrame(columns=["chapter", "verse", "speaker", "sanskrit", "translation", "commentary"])

    # Iterate through chapters (1 to 18)
    for chapter_no in range(1, 19):
        chapter_url = base_url + f"chapter/{chapter_no}/"
        print(f"Processing chapter {chapter_no}...")
        
        # Extract verse links for the chapter
        verse_links = extract_verse_links(chapter_url)
        print(f"Found {len(verse_links)} verses in chapter {chapter_no}.")
        
        # Iterate through verse links
        for verse_link in verse_links:
            verse_no = verse_link.split("/")[-1]
            print(f"Processing chapter {chapter_no}, verse {verse_no}...")
            
            # Construct full verse URL
            verse_url = base_url + verse_link.lstrip("/")
            
            # Extract commentary
            commentary = extract_commentary(verse_url)
            print(f"Commentary extracted for chapter {chapter_no}, verse {verse_no}.")
            
            # Update the DataFrame
            mask = (df["chapter"] == chapter_no) & (df["verse"] == int(verse_no))
            if mask.any():
                # Update existing row
                df.loc[mask, "commentary"] = commentary
            else:
                # Add new row using pd.concat (recommended alternative to append)
                new_row = pd.DataFrame({
                    "chapter": [chapter_no],
                    "verse": [int(verse_no)],
                    "speaker": [""],  # Placeholder (can be updated later)
                    "sanskrit": [""],  # Placeholder (can be updated later)
                    "translation": [""],  # Placeholder (can be updated later)
                    "commentary": [commentary]
                })
                df = pd.concat([df, new_row], ignore_index=True)
            
            # Add a 5-second delay between verse requests
            time.sleep(5)
        
        # Save progress after each chapter
        df.to_csv("data/processed/info_temp.csv", index=False)
        print(f"Progress saved after chapter {chapter_no}.")
    
    # Save final CSV
    df.to_csv("data/processed/info.csv", index=False)
    print("Verse data scraped and saved to CSV.")

# Run the script
if __name__ == "__main__":
    process_verses()