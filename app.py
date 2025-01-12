from sqlalchemy import Table, Column, Integer, Text as SQLText, MetaData, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.table import Table as RichTable
import sys
import unicodedata
from rich.padding import Padding
from rich.style import Style
import locale
from mistralai import Mistral
from flask import Flask, jsonify, request, render_template, url_for
from flask_cors import CORS

app = Flask(__name__,
    static_folder='static',
    template_folder='templates')
CORS(app)

# Set locale for proper Unicode handling
locale.setlocale(locale.LC_ALL, '')

# Initialize Rich console with Unicode support
console = Console(force_terminal=True, force_interactive=True, color_system="truecolor")

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env file")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY not set in .env file")

# Initialize Mistral client
mistral_client = Mistral(api_key=MISTRAL_API_KEY)
MISTRAL_MODEL = "mistral-large-latest"

# Initialize SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Initialize Mistral client
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY not set in .env file")

model = "mistral-large-latest"
mistral_client = Mistral(api_key=MISTRAL_API_KEY)

# Define the metadata and tables
metadata = MetaData()
model = SentenceTransformer('all-MiniLM-L6-v2')

# Define tables with correct SQLAlchemy Text type
questions_table = Table(
    "questions",
    metadata,
    Column("question_id", Integer, primary_key=True),
    Column("chapter_no", Integer),
    Column("verse_no", Integer),
    Column("possible_question", SQLText),
    Column("question_embedding", SQLText)
)

info_table = Table(
    "info",
    metadata,
    Column("chapter_no", Integer, primary_key=True),
    Column("verse_no", Integer, primary_key=True),
    Column("sanskrit_verse", SQLText),
    Column("speaker_name", SQLText),
    Column("english_translations", SQLText),
    Column("commentary", SQLText),
    Column("translation_embedding", SQLText),
    Column("commentary_embedding", SQLText)
)

chapter_table = Table(
    "chapter",
    metadata,
    Column("chapter_no", Integer, primary_key=True),
    Column("chapter_heading", SQLText),
    Column("chapter_desc_heading", SQLText),
    Column("chapter_intro", SQLText)
)

def query_to_embedding(query: str) -> str:
    """
    Converts a user query into a vector embedding.
    """
    embedding = model.encode(query)
    return "[" + ",".join(map(str, embedding)) + "]"

def search_across_embeddings(query: str, limit: int = 5) -> List[Tuple[int, int, float, str]]:
    """
    Searches for the most similar content across questions, translations, and commentaries.
    
    Args:
        query (str): The user's query
        limit (int): Number of results to return per embedding type
    
    Returns:
        List[Tuple[int, int, float, str]]: List of (chapter_no, verse_no, similarity_score, source)
    """
    query_embedding = query_to_embedding(query)
    results = []
    
    # Search in questions
    question_query = select(
        questions_table.c.chapter_no,
        questions_table.c.verse_no,
        (questions_table.c.question_embedding.op('<=>')(query_embedding)).label("similarity")
    ).order_by(
        questions_table.c.question_embedding.op('<=>')(query_embedding)
    ).limit(limit)
    
    question_results = [(r[0], r[1], r[2], 'question') for r in session.execute(question_query)]
    results.extend(question_results)
    
    # Search in translations
    translation_query = select(
        info_table.c.chapter_no,
        info_table.c.verse_no,
        (info_table.c.translation_embedding.op('<=>')(query_embedding)).label("similarity")
    ).order_by(
        info_table.c.translation_embedding.op('<=>')(query_embedding)
    ).limit(limit)
    
    translation_results = [(r[0], r[1], r[2], 'translation') for r in session.execute(translation_query)]
    results.extend(translation_results)
    
    # Search in commentaries
    commentary_query = select(
        info_table.c.chapter_no,
        info_table.c.verse_no,
        (info_table.c.commentary_embedding.op('<=>')(query_embedding)).label("similarity")
    ).order_by(
        info_table.c.commentary_embedding.op('<=>')(query_embedding)
    ).limit(limit)
    
    commentary_results = [(r[0], r[1], r[2], 'commentary') for r in session.execute(commentary_query)]
    results.extend(commentary_results)
    
    # Sort all results by similarity score
    results.sort(key=lambda x: x[2])
    
    return results

def get_verse_details(chapter_no: int, verse_no: int) -> Dict:
    """
    Fetches detailed information about a specific verse from the info table.
    
    Args:
        chapter_no (int): Chapter number
        verse_no (int): Verse number
    
    Returns:
        Dict: Verse details including sanskrit verse, speaker, and translation
    """
    query = select(
        info_table.c.sanskrit_verse,
        info_table.c.speaker_name,
        info_table.c.english_translations,
        info_table.c.commentary
    ).where(
        (info_table.c.chapter_no == chapter_no) &
        (info_table.c.verse_no == verse_no)
    )
    
    result = session.execute(query).first()
    if result:
        return {
            "chapter_no": chapter_no,
            "verse_no": verse_no,
            "sanskrit_verse": result[0],
            "speaker": result[1],
            "translation": result[2],
            "commentary": result[3]
        }
    return None

def get_best_match_with_details(query: str) -> Dict:
    """
    Gets the single best matching verse across all embedding types along with its details.
    
    Args:
        query (str): The user's query
    
    Returns:
        Dict: Complete verse information including match details and verse content
    """
    results = search_across_embeddings(query, limit=1)
    if not results:
        return None
        
    chapter_no, verse_no, similarity, source = results[0]
    verse_details = get_verse_details(chapter_no, verse_no)
    
    if verse_details:
        verse_details.update({
            "similarity_score": similarity,
            "match_source": source
        })
    
    return verse_details

def normalize_sanskrit(text: str) -> str:
    """
    Normalizes Sanskrit text for proper display.
    """
    if not text:
        return ""
    # Normalize Unicode characters
    normalized = unicodedata.normalize('NFC', text)
    # Add proper spacing for verses
    parts = normalized.split('||')
    if len(parts) > 1:
        return " || ".join(part.strip() for part in parts)
    return normalized


def create_styled_text(text: str, style: str = None) -> Text:
    """
    Creates styled text with proper word wrapping.
    """
    styled_text = Text(text, style=style)
    styled_text.overflow = "fold"
    return styled_text

def generate_verse_summary(translation: str, commentary: str) -> str:
    """
    Generates a summary of the verse using Mistral AI.
    
    Args:
        translation (str): English translation of the verse
        commentary (str): Commentary on the verse
    
    Returns:
        str: Generated summary
    """
    prompt = f"""Given this verse from the Bhagavad Gita:

Translation:
{translation}

Commentary:
{commentary}

Please provide a concise summary (2-3 sentences) of the main teaching or message from this verse."""

    try:
        response = mistral_client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        console.print(f"Error generating summary: {str(e)}", style="bold red")
        return "Summary generation failed. Please refer to the translation and commentary above."

def display_verse(verse_details: Dict):
    """
    Displays verse details with generated summary using Rich.
    """
    # Create header
    header = Text()
    header.append("॥ श्रीमद्भगवद्गीता ॥\n", style="bold cyan")
    header.append(f"Chapter {verse_details['chapter_no']}, Verse {verse_details['verse_no']}\n", style="bold cyan")
    header.append(f"Speaker: {verse_details['speaker']}", style="yellow")
    
    # Create panel for Sanskrit verse with proper formatting
    sanskrit_text = normalize_sanskrit(verse_details['sanskrit_verse'])
    sanskrit_styled = create_styled_text(sanskrit_text, "bold magenta")
    sanskrit_panel = Panel(
        Padding(sanskrit_styled, (1, 2)),
        title="॥ श्लोक ॥",
        border_style="bright_blue",
        box=box.DOUBLE_EDGE,
        title_align="center",
        width=100
    )
    
    # Generate summary using Mistral
    with console.status("[bold green]Generating verse summary..."):
        summary = generate_verse_summary(verse_details['translation'], verse_details['commentary'])
    
    # Create panel for summary
    summary_styled = create_styled_text(summary)
    summary_panel = Panel(
        Padding(summary_styled, (1, 2)),
        title="AI-Generated Summary",
        border_style="cyan",
        box=box.DOUBLE_EDGE,
        title_align="center",
        width=100
    )
    
    # Create match information table
    match_info = RichTable(
        show_header=True,
        box=box.SIMPLE_HEAD,
        title="Match Information",
        width=100
    )
    match_info.add_column("Match Source", style="cyan", justify="center")
    match_info.add_column("Similarity Score", style="cyan", justify="center")
    match_info.add_row(
        verse_details['match_source'],
        f"{verse_details['similarity_score']:.4f}"
    )

    # Print everything with proper spacing
    console.print("\n")
    console.print(Padding(header, (1, 2)))
    console.print(sanskrit_panel)
    console.print(summary_panel)
    console.print(match_info)
    console.print("\n")

def display_welcome():
    """
    Displays welcome message and instructions.
    """
    welcome_text = Text()
    welcome_text.append("\n🕉️  श्रीमद्भगवद्गीता  🕉️\n\n", style="bold cyan")
    welcome_text.append("Ask any question about the Bhagavad Gita or use these commands:\n\n", style="yellow")
    welcome_text.append("- 'EXIT' to quit\n", style="green")
    welcome_text.append("- 'HELP' for instructions\n", style="green")
    
    console.print(Panel(
        welcome_text,
        title="Bhagavad Gita Search",
        border_style="cyan",
        box=box.DOUBLE_EDGE,
        width=100
    ))

def display_help():
    """
    Displays help information.
    """
    help_text = Text()
    help_text.append("\nAvailable Commands:\n", style="bold yellow")
    help_text.append("- Type your question in natural language\n", style="green")
    help_text.append("- Type 'EXIT' to quit the application\n", style="green")
    help_text.append("- Type 'HELP' to see this message again\n\n", style="green")
    help_text.append("Example Questions:\n", style="bold yellow")
    help_text.append("- What does Krishna say about dharma?\n", style="cyan")
    help_text.append("- How can I achieve peace of mind?\n", style="cyan")
    help_text.append("- What is karma yoga?\n", style="cyan")
    
    console.print(Panel(
        help_text,
        title="Help",
        border_style="yellow",
        box=box.DOUBLE_EDGE,
        width=100
    ))

@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    try:
        query = request.json.get('query')
        if not query:
            return jsonify({'error': 'Query is required'}), 400
            
        result = get_best_match_with_details(query)
        if result:
            # Generate summary for the verse
            summary = generate_verse_summary(result['translation'], result['commentary'])
            result['summary'] = summary
            return jsonify(result)
        return jsonify({'error': 'No matching verses found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)