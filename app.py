#%%
import os
import uuid # Added
import pickle # Added for caching
import hashlib # Add this import at the top of app.py
from flask import Flask, request, jsonify # ensure jsonify is imported
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
import numpy as np
from datetime import datetime, timezone # Added timezone
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam # Added
from sqlalchemy import desc # Make sure to import desc

# Assuming db.py and models.py are in the root or an accessible Python module path
from db import db
import models # This import is important so Alembic can find the models
# from models import Conversation # Your Conversation model <- Removed as we use models.Conversation

load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Database Configuration ---
# Prioritize DATABASE_URL from environment, fallback to local SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///creditrobot.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Recommended to disable

# Initialize SQLAlchemy with the app
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Set up the OpenAI client
# Load the API key from an environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("[ERROR] The OPENAI_API_KEY environment variable is not set.")
    print("Please set it before running the application.")
    # You might want to exit here if the key is crucial for startup
    # import sys
    # sys.exit(1) 
client = OpenAI(api_key=api_key)

DOCS = []  # We'll store embedded documents here.
BASE_PROJECT_DIR = "" # Define base directory for the project - Corrected: script runs from within CreditROBOT
CACHE_PATH = os.path.join(BASE_PROJECT_DIR, "embeddings_cache.pkl")  # Cache file inside CreditROBOT

def compute_embedding(text, model="text-embedding-ada-002"):
    """Use the new OpenAI client syntax to compute embedding for a given text."""
    response = client.embeddings.create(model=model, input=[text])
    embedding = response.data[0].embedding
    return embedding

def cosine_similarity(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return dot / (norm_a * norm_b)

def scan_language_folders():
    """
    Recursively scans the four folders:
      - "Description Deutsch"
      - "Description Französisch"
      - "Description Italienisch"
      - "Description English"
    Each .md file is read & embedded as a separate 'document'.
    Implements caching to avoid re-embedding unchanged files.
    """
    # Load existing cache if available
    embeddings_cache = {}
    # Ensure the cache path is correct relative to where the script is run from
    # If CACHE_PATH is now "CreditROBOT/embeddings_cache.pkl", os.path.exists will check correctly from c:/Codes/CRChatbot
    if os.path.exists(CACHE_PATH):
        try:
            # Create instance directory if CACHE_PATH is in instance_path and it doesn't exist
            # cache_dir = os.path.dirname(CACHE_PATH)
            # if cache_dir and not os.path.exists(cache_dir):
            #    os.makedirs(cache_dir) # Not strictly needed if CACHE_PATH is CreditROBOT/embeddings_cache.pkl

            with open(CACHE_PATH, "rb") as f:
                embeddings_cache = pickle.load(f)
                print(f"Loaded {len(embeddings_cache)} cached embeddings from {CACHE_PATH}")
        except (pickle.UnpicklingError, EOFError, FileNotFoundError) as e: # Added FileNotFoundError
            print(f"[WARN] Could not load cache file {CACHE_PATH}: {e}. Starting with an empty cache.")
            embeddings_cache = {} # Ensure cache is empty on error
    
    # DOCS will be populated here instead of being a global modified directly
    local_docs = [] 
    updated_cache = {}  # New cache data to save at the end
    
    folders = [
        ("Description Deutsch", "de"),
        ("Description Französisch", "fr"),
        ("Description Italienisch", "it"),
        ("Description English", "en"),
    ]

    for folder_name, lang_code in folders:
        # Construct the full path to the language folder relative to the project base
        actual_folder_path = os.path.join(BASE_PROJECT_DIR, folder_name)

        if not os.path.exists(actual_folder_path):
            print(f"[WARN] Folder {actual_folder_path} does not exist, skipping.")
            continue
        
        for filename in os.listdir(actual_folder_path):
            if not filename.lower().endswith(".md"):
                continue  # skip non-Markdown files
            
            file_path = os.path.join(actual_folder_path, filename)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
            except Exception as e:
                print(f"[ERROR] Could not read file {file_path}: {e}")
                continue

            if not text_content.strip():
                print(f"[WARN] Skipping empty file: {file_path}")
                continue
                
            file_mod_time = os.path.getmtime(file_path)
            embedding = None
            
            if file_path in embeddings_cache:
                cached_entry = embeddings_cache[file_path]
                if ("last_modified" in cached_entry and 
                        cached_entry.get("last_modified") == file_mod_time and
                        "embedding" in cached_entry and cached_entry["embedding"]): # Ensure embedding exists
                    embedding = cached_entry["embedding"]
                    print(f"Using cached embedding for: {file_path}")
            
            if embedding is None:
                print(f"Computing embedding for: {file_path}")
                try:
                    embedding = compute_embedding(text_content)
                except Exception as e:
                    print(f"[ERROR] Failed to compute embedding for {file_path}: {e}")
                    continue # Skip this file if embedding fails
            
            if embedding is not None: # Ensure embedding was successfully obtained
                updated_cache[file_path] = {
                    "embedding": embedding,
                    "last_modified": file_mod_time
                }
                local_docs.append({
                    "language": lang_code,
                    "filepath": file_path,
                    "content": text_content,
                    "embedding": embedding
                })
            else:
                print(f"[WARN] Embedding is None for {file_path}, not adding to docs or cache.")

    # After processing all files, save the updated cache to disk
    try:
        with open(CACHE_PATH, "wb") as f:
            pickle.dump(updated_cache, f)
        print(f"Saved {len(updated_cache)} embeddings to {CACHE_PATH}")
    except Exception as e:
        print(f"[ERROR] Could not save cache file {CACHE_PATH}: {e}")

    # Update the global DOCS variable
    global DOCS
    DOCS = local_docs
    # No return needed as DOCS is global, but good practice if it were not

def retrieve_best_doc(user_query, user_lang=None):
    """
    1) Embeds user_query
    2) Optionally filters DOCS by user_lang
    3) Calculates cosine similarity to each doc
    4) Returns the best doc + similarity score
    """
    query_emb = compute_embedding(user_query)

    best_doc = None
    best_score = -1

    for doc in DOCS:
        # If you want cross-lingual retrieval, remove the language check:
        if user_lang and (doc["language"] != user_lang):
            continue

        score = cosine_similarity(query_emb, doc["embedding"])
        if score > best_score:
            best_score = score
            best_doc = doc

    return best_doc, best_score

def load_base_prompt(language='de'):
    """Return a short system prompt in the user's language."""
    if language == 'de':
        return """
Antworte auf Deutsch.

**Rolle:**  
Du bist ein hochspezialisierter Assistent der Creditreform, der präzise und kompetente Antworten zu Bonitätsinformationen, Inkasso und weiteren Creditreform-Dienstleistungen liefert.

Hier sind Kontext-Infos aus dem passenden Dokument:
        """
    elif language == 'fr':
        return """
Réponds en français.
Rôle :
Tu es un assistant hautement spécialisé de Creditreform, fournissant des réponses précises et compétentes concernant les informations de solvabilité, le recouvrement de créances et d'autres services proposés par Creditreform.

Voici des informations contextuelles issues du document correspondant :        
        """    
    elif language == 'it':
        return """
Rispondi in italiano.
Ruolo:
Sei un assistente altamente specializzato di Creditreform, in grado di fornire risposte precise e competenti riguardo alle informazioni sulla solvibilità, al recupero crediti e ad altri servizi offerti da Creditreform.

Ecco le informazioni contestuali tratte dal documento corrispondente:
        """
    elif language == 'en':
        return """
Respond in English.

**Role:**  
You are a highly-specialised Creditreform assistant who provides precise, expert answers about creditworthiness information, debt-collection and other Creditreform services.

Here is contextual information taken from the relevant document:
    """
    else:
        # fallback if unknown
        return "You are a Creditreform assistant. Please answer in HTML."
    

def load_final_prompt(language='de'):
    """Return a short system prompt in the user's language."""
    if language == 'de':
        return """
**Antwortformat**
- Antworten ausschließlich in HTML
- Verwende Absätze <p> für Fließtext
- Verwende Überschriften <h4> für Titel
- Verwende Listen <ul>, <li> für Aufzählungen

Am allerwichtigste:
DU MUSST IMMER ALLE LINKS AUSGEBEN. WENN VORHANDEN IN DER RICHTIGEN SPRACHE
HALTE DICH KURZ
WENN DU NICHT SICHER BIST BEI DEINER ANTWORT VERWEISE AUF DAS KONTAKTFORMULAR: https://www.creditreform.ch/creditreform/kontakt
        """
    elif language == 'fr':
        return """
**Format de réponse**  
- Répondre exclusivement en HTML  
- Utiliser les paragraphes `<p>` pour le texte courant  
- Utiliser les titres `<h4>` pour les en-têtes  
- Utiliser les listes `<ul>`, `<li>` pour les énumérations  

Le plus important :  
TU DOIS TOUJOURS FOURNIR TOUS LES LIENS  
SOIS CONCIS  
SI TU N’ES PAS SÛR DE TA RÉPONSE, RENVOIE AU FORMULAIRE DE CONTACT :  
[https://www.creditreform.ch/creditreform/kontakt](https://www.creditreform.ch/creditreform/kontakt)

        """    
    elif language == 'it':
        return """
**Formato di risposta**  
- Rispondere esclusivamente in HTML  
- Utilizzare paragrafi `<p>` per il testo continuo  
- Utilizzare intestazioni `<h4>` per i titoli  
- Utilizzare liste `<ul>`, `<li>` per gli elenchi  

La cosa più importante:  
DEVI SEMPRE FORNIRE TUTTI I LINK  
MANTIENITI BREVE  
SE NON SEI SICURO DELLA TUA RISPOSTA, RIMANDA AL MODULO DI CONTATTO:  
[https://www.creditreform.ch/creditreform/kontakt](https://www.creditreform.ch/creditreform/kontakt)
"""
    elif language == 'en':
        return """
**Answer format**
- Answer *exclusively* in HTML
- Use paragraphs `<p>` for continuous text
- Use headings `<h4>` for titles
- Use lists `<ul>`, `<li>` for bullet points

Most important:
YOU MUST ALWAYS OUTPUT *ALL* LINKS. BUT IF POSSIBLE CHOOSE THE ONE IN THE CORRECT LANGUAGE
KEEP IT SHORT  
IF YOU ARE NOT SURE ABOUT YOUR ANSWER, REFER TO THE CONTACT FORM:  
https://www.creditreform.ch/creditreform/kontakt
"""
    else:
        # fallback if unknown
        return "Please answer in HTML."

def get_or_create_session(session_id: str) -> models.Session:
    """Fetches a session from the DB or creates it if it doesn't exist."""
    session = db.session.query(models.Session).filter_by(session_id=session_id).first()
    if not session:
        print(f"Creating new session for ID: {session_id}")
        session = models.Session(session_id=session_id)
        db.session.add(session)
        # We commit here so the session is available immediately for the rest of the request
        # A more advanced pattern could pass the session object around without this intermediate commit.
        db.session.commit()
    return session

def update_conversation_summary(session: models.Session, user_message: str, assistant_message: str):
    """Updates the session's running summary using a fast LLM."""
    
    current_summary = session.conversation_summary
    
    # This is a highly specific prompt for the summarization task
    summarizer_prompt = f"""
    Your task is to update a conversation summary. You will be given the previous summary
    and the latest user-assistant interaction. Integrate the new information from the interaction
    into the summary concisely. Preserve key details, names, topics, and user goals.
    The user is asking about Creditreform.

    PREVIOUS SUMMARY:
    "{current_summary}"

    LATEST INTERACTION:
    User: "{user_message}"
    Assistant: "{assistant_message}"

    UPDATED SUMMARY:
    """
    
    try:
        response = client.chat.completions.create(
            # Use a fast and cheap model for this summarization task
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert conversation summarizer."},
                {"role": "user", "content": summarizer_prompt}
            ],
            temperature=0.2,
            max_tokens=250 # Keep the summary concise
        )
        new_summary = response.choices[0].message.content
        
        # Update the summary on the session object in memory
        session.conversation_summary = new_summary.strip() if new_summary else current_summary
        # The calling function will be responsible for the final db.session.commit()
        
    except Exception as e:
        app.logger.error(f"Failed to update conversation summary for session {session.session_id}: {e}")
        # If summarization fails, we don't crash. The old summary will be used next time.

def generate_llm_cache_key(user_message: str, retrieved_doc_content: str | None, conversation_summary: str | None, language: str) -> str:
    """
    Generates a SHA256 hash key for caching LLM responses.
    The key is based on the user's message, the content of the retrieved document (if any),
    the current conversation summary, and the language.
    """
    key_string = f"{user_message.strip()}|" \
                 f"{retrieved_doc_content.strip() if retrieved_doc_content else 'NO_DOC'}|" \
                 f"{conversation_summary.strip() if conversation_summary else 'NO_SUMMARY'}|" \
                 f"{language.strip()}"

    return hashlib.sha256(key_string.encode('utf-8')).hexdigest()

########################################################
# Function to get history
def get_history(session_id_to_fetch, limit=20):
    """
    Retrieves conversation history for a given session_id, ordered oldest to newest.
    Returns a list of dictionaries suitable for LLM context.
    """
    if not session_id_to_fetch:
        return []

    rows = db.session.execute(
        db.select(models.Conversation) # Use models.Conversation
          .where(models.Conversation.session_uuid == session_id_to_fetch) # Changed session_id to session_uuid
          .order_by(models.Conversation.timestamp.asc()) # ASC for oldest first
          .limit(limit)
    ).scalars().all()
    
    history_for_llm = []
    for row in rows:
        history_for_llm.append({"role": row.role, "content": row.content})
    
    return history_for_llm

########################################################
# 2) FLASK ROUTES
########################################################

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    session_id_str = data.get('sessionId') or str(uuid.uuid4())
    user_message = data.get('message', '').strip()
    language = (data.get('lang') or 'de')[:5].lower()

    if not user_message:
        return jsonify({"error": "Empty message received"}), 400

    session = get_or_create_session(session_id_str) # models.Session object

    user_entry = models.Conversation(session_uuid=session.session_id, role='user', language=language, content=user_message)
    db.session.add(user_entry)

    try:
        best_doc, score = retrieve_best_doc(user_message, user_lang=language)
        retrieved_doc_content = best_doc['content'] if best_doc else None
        doc_path_for_assistant_entry = best_doc['filepath'] if best_doc else None
        similarity_for_assistant_entry = score if best_doc else None
    except Exception as e: # Catching potential errors from RAG, e.g. OpenAI key error during embedding
        app.logger.error(f"RAG (retrieve_best_doc) failed: {e}")
        best_doc = None # Ensure best_doc is None so flow continues predictably
        retrieved_doc_content = None
        doc_path_for_assistant_entry = None
        similarity_for_assistant_entry = None

    bot_response_content = None  # Initialize

    # CACHE LOOKUP
    # Ensure session.conversation_summary is available here
    cache_key = generate_llm_cache_key(user_message, retrieved_doc_content, session.conversation_summary, language)
    cached_item = db.session.query(models.LlmResponseCache).filter_by(cache_key=cache_key).first()

    if cached_item:
        # Optional: Add TTL check here if desired
        # if (datetime.now(timezone.utc) - cached_item.created_at) < timedelta(days=YOUR_TTL_DAYS):
        app.logger.info(f"Cache HIT for key: {cache_key[:10]}...") # Ensure app.logger is configured
        bot_response_content = cached_item.llm_response
        cached_item.last_accessed_at = datetime.now(timezone.utc)
        db.session.add(cached_item)
        doc_path_for_assistant_entry = cached_item.source_document_path
        similarity_for_assistant_entry = None
        # else:
        #   app.logger.info(f"Cache STALE for key: {cache_key[:10]}... Treating as miss.")
        #   cached_item = None # Ensure it's treated as a miss, so bot_response_content remains None

    if bot_response_content is None:
        app.logger.info(f"Cache MISS for key: {cache_key[:10]}... Calling LLM.")
        base_prompt_text = load_base_prompt(language) # Renamed to avoid conflict
        final_prompt_text = load_final_prompt(language) # Renamed to avoid conflict

        # Ensure session.conversation_summary is correctly used
        contextual_history = f"CONTEXT FROM PREVIOUSLY IN THE CONVERSATION:\n{session.conversation_summary}"

        system_prompt = (
            f"{base_prompt_text}\n\n"
            f"{contextual_history}\n\n"
            f"CONTEXT FROM KNOWLEDGE BASE DOCUMENT '{doc_path_for_assistant_entry}':\n{retrieved_doc_content}\n" # Use determined doc path and content
            f"---\n"
            f"{final_prompt_text}\n"
        ) if best_doc else f"{base_prompt_text}\n\n{contextual_history}\n\n(No matching document found.)\n---\n{final_prompt_text}"

        llm_call_succeeded = False # Flag
        try:
            # Ensure client, ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam are defined
            llm_api_response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    ChatCompletionSystemMessageParam(role="system", content=system_prompt),
                    ChatCompletionUserMessageParam(role="user", content=user_message)
                ],
                max_tokens=700,
                temperature=0.0
            )
            llm_response_str = llm_api_response.choices[0].message.content or "" # Renamed
            bot_response_content = llm_response_str.replace("```html", "").replace("```", "")
            llm_call_succeeded = True # Mark as success
        except Exception as e:
            app.logger.error(f"LLM API call failed: {e}")
            bot_response_content = "I am sorry, but I encountered an error. Please try again."
            # llm_call_succeeded remains False

        if llm_call_succeeded and bot_response_content: # Cache only on success and if content exists
            new_cache_entry = models.LlmResponseCache(
                cache_key=cache_key,
                llm_response=bot_response_content,
                language=language,
                source_document_path=doc_path_for_assistant_entry
            )
            db.session.add(new_cache_entry)

    assistant_entry = models.Conversation(
        session_uuid=session.session_id,
        role='assistant',
        language=language,
        content=bot_response_content, # This is now from cache or LLM
        doc_path=doc_path_for_assistant_entry,
        similarity=similarity_for_assistant_entry
    )
    db.session.add(assistant_entry)

    # update_conversation_summary must be called AFTER bot_response_content is finalized
    update_conversation_summary(session, user_message, bot_response_content)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Database commit failed: {e}")
        return jsonify({"error": "Could not save conversation."}), 500

    return jsonify({
        'response': bot_response_content,
        'sessionId': session_id_str
    })

@app.route('/')
def index():
    """
    Return the original front-end HTML (the same code you used before).
    Make sure 'index.html' is present in the same directory as this app.
    """
    try:
        with open('index.html', 'r', encoding='utf-8') as file:
            html_content = file.read()
        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        # Fallback if 'index.html' is not found
        return "<h3>Creditreform Multi-Topic Chatbot (Embedding-based)</h3>", 200

########################################################
# 3) ENTRY POINT
########################################################

if __name__ == '__main__':
    # On startup, read & embed all .txt files from the 3 language folders
    scan_language_folders()

    if not client.api_key:
        print("[WARNING] No OpenAI API key set.")
    app.run(host='0.0.0.0', port=5000, debug=True)

# %%
