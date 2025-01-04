import requests
from bs4 import BeautifulSoup
import pandas as pd

# Base URL and chapter list
base_url = "https://www.holy-bhagavad-gita.org/"
chapters = [str(i) for i in range(1, 19)]

# Function to scrape chapter data
def scrape_chapter_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Extract chapter title
    chapter_title = soup.find("h4", class_="chapterTitle").text.strip()
    
    # Extract chapter description heading
    chapter_desc_heading = soup.find("p", class_="chapterDescHeading").text.strip()
    
    # Extract chapter introduction
    chapter_intro = soup.find("div", class_="chapterIntro").text.strip()
    
    return {
        "chapter_title": chapter_title,
        "chapter_desc_heading": chapter_desc_heading,
        "chapter_intro": chapter_intro
    }

# Scrape data for all chapters
data = []
for chapter in chapters:
    url = base_url + "chapter/" + chapter + "/"
    chapter_data = scrape_chapter_data(url)
    chapter_data["chapter_no"] = int(chapter)
    data.append(chapter_data)

# Save to CSV
df = pd.DataFrame(data)
df.to_csv("data/scraped/chapters.csv", index=False)
print("Chapter data scraped and saved to CSV.")