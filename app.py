from sqlalchemy import Table, Column, Integer, Text as SQLText, MetaData, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict
import os
from dotenv import load_dotenv
from mistralai import Mistral
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Load environment variables
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

# Initialize SQLAlchemy engine and session, this postgres:: is needed for sqlalchemy 1.4 and above
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

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

pys_question_table = Table(
    "pys_question",
    metadata,
    Column("question_id", Integer, primary_key=True),
    Column("chapter_no", Integer),
    Column("verse_no", Integer),
    Column("sanskrit", SQLText),
    Column("translation", SQLText),
    Column("possible_question", SQLText),
    Column("question_embedding", SQLText)
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
        return "Summary generation failed. Please refer to the translation and commentary above."
    
def search_pys_questions(query: str, limit: int = 5) -> List[Dict]:
    """
    Searches for similar questions in the pys_question table using vector embeddings.
    
    Args:
        query (str): The user's query
        limit (int): Number of results to return
    
    Returns:
        List[Dict]: List of matching verses with their details
    """
    query_embedding = query_to_embedding(query)
    
    # Search in pys_questions
    search_query = select(
        pys_question_table.c.chapter_no,
        pys_question_table.c.verse_no,
        pys_question_table.c.sanskrit,
        pys_question_table.c.translation,
        pys_question_table.c.possible_question,
        (pys_question_table.c.question_embedding.op('<=>')(query_embedding)).label("similarity")
    ).order_by(
        pys_question_table.c.question_embedding.op('<=>')(query_embedding)
    ).limit(limit)
    
    results = []
    for row in session.execute(search_query):
        results.append({
            "chapter_no": row.chapter_no,
            "verse_no": row.verse_no,
            "sanskrit": row.sanskrit,
            "translation": row.translation,
        })
    
    return results[0]

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
    
@app.route('/api/search_pys', methods=['POST'])
def search_pys():
    try:
        query = request.json.get('query')
        if not query:
            return jsonify({'error': 'Query is required'}), 400
            
        results = search_pys_questions(query, limit=5)  # You can adjust the limit as needed
        if results:
            return jsonify(results)
        return jsonify({'error': 'No matching verses found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)