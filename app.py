#%%
import os
import uuid # Added
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
    Each .txt file is read & embedded as a separate 'document'.
    """
    folders = [
        ("Description Deutsch", "de"),
        ("Description Französisch", "fr"),
        ("Description Italienisch", "it"),  # <-- Temporarily commented out
        ("Description English", "en"),
    ]
    for folder_path, lang_code in folders:
        if not os.path.exists(folder_path):
            print(f"[WARN] Folder {folder_path} does not exist, skipping.")
            continue
        # List all .md files in that folder
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".md"):
                full_path = os.path.join(folder_path, filename)
                with open(full_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
                print(f"Processing file: {full_path}, Length: {len(text_content)}")
                
                # Compute embedding
                if not text_content.strip():
                    print(f"[WARN] Skipping empty file: {full_path}")
                    continue

                emb = compute_embedding(text_content)
                DOCS.append({
                    "language": lang_code,
                    "filepath": full_path,
                    "content": text_content,
                    "embedding": emb
                })
                print(f"Embedded file: {full_path} (lang={lang_code})")

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
          .where(models.Conversation.session_id == session_id_to_fetch)
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
    
    # 1. Get or ensure session_id
    session_id_str = data.get('sessionId')
    if not session_id_str:
        session_id_str = str(uuid.uuid4())
    
    user_message = data.get('message', '').strip()
    language = (data.get('lang') or 'de')[:5].lower()

    if not user_message:
        return jsonify({"error": "Empty message received"}), 400

    # --- Persist User Message ---
    user_entry = models.Conversation(
        session_id=session_id_str,
        role='user',
        language=language,
        content=user_message
    )
    db.session.add(user_entry)

    # --- Existing logic for language detection, RAG, LLM call ---
    # Retrieve best doc for the user query
    best_doc, score = retrieve_best_doc(user_message, user_lang=language)

    # Placeholder for RAG details (replace with actual values from your RAG logic)
    match_path_placeholder = None
    match_score_placeholder = None
    if best_doc:
        match_path_placeholder = best_doc['filepath']
        match_score_placeholder = score
        print(f"Best match: {best_doc['filepath']} (score={score:.3f})")
        base_prompt = load_base_prompt(language)
        final_prompt = load_final_prompt(language)
        system_prompt = (
            f"{base_prompt}\n\n"
            f"{best_doc['content']}\n"
            f"---\n"
            f"{final_prompt}\n"
        )
    else:
        # fallback: no doc found or the folder was empty
        system_prompt = load_base_prompt(language)
        system_prompt += "\n\n(Keine passenden Dokumente gefunden.)\n"

    # --- Integrate History for LLM Call ---
    # 1. Retrieve conversation history
    conversation_history = get_history(session_id_str, limit=10) # Adjust limit as needed

    # 2. Prepare messages for LLM
    messages_for_llm = []
    for entry in conversation_history:
        messages_for_llm.append({"role": entry["role"], "content": entry["content"]})
    
    # Add current system prompt (if you want to reiterate it - or adjust based on LLM needs)
    # For many models, the system prompt is a one-time setup for the conversation.
    # If your system_prompt is dynamic per turn (e.g. includes RAG context), 
    # you might structure messages_for_llm differently, e.g.,
    # messages_for_llm = [{"role": "system", "content": system_prompt}] + history_messages + [{"role": "user", "content": user_message}]
    # For now, let's assume system_prompt is passed as a separate parameter or at the start of messages.
    # The example in the plan adds user message after history.
    
    # Add current user message to the history for the LLM
    messages_for_llm.append({"role": "user", "content": user_message}) # This is the current user message added to historical messages

    # Construct type-safe messages for OpenAI API
    typed_llm_input_messages: list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam] = [
        ChatCompletionSystemMessageParam(role="system", content=system_prompt)
    ]
    # conversation_history already contains the current user's message if messages_for_llm was built from it.
    # The plan's logic for messages_for_llm:
    # 1. conversation_history = get_history(...)
    # 2. messages_for_llm = [] from conversation_history
    # 3. messages_for_llm.append({"role": "user", "content": user_message}) <-- current user message
    # 4. llm_input_messages = [{"role": "system", "content": system_prompt}] + messages_for_llm
    # So, messages_for_llm contains historical user/assistant turns AND the current user message.

    # Let's rebuild typed_llm_input_messages from messages_for_llm (which includes history + current user message)
    # and prepend the system prompt.
    
    # messages_for_llm was:
    # history_entries = []
    # for entry in conversation_history: # from get_history (oldest first)
    #    history_entries.append({"role": entry["role"], "content": entry["content"]})
    # history_entries.append({"role": "user", "content": user_message}) # current user message
    # This is what messages_for_llm variable holds.

    for msg_data in messages_for_llm: # messages_for_llm contains history AND current user message
        role = msg_data.get("role")
        content = msg_data.get("content", "")
        if role == "user":
            typed_llm_input_messages.append(ChatCompletionUserMessageParam(role="user", content=content))
        elif role == "assistant":
            typed_llm_input_messages.append(ChatCompletionAssistantMessageParam(role="assistant", content=content))
        # System message is already added as the first element.
    
    app.logger.info(f"Messages for LLM (Session: {session_id_str}): {typed_llm_input_messages}")

    try:
        llm_api_response = client.chat.completions.create(
            model="gpt-4o", # Or your chosen model
            messages=typed_llm_input_messages, # Pass the type-safe list
            max_tokens=700,
            temperature=0.0
        )
        bot_response_content = llm_api_response.choices[0].message.content
        bot_response_content = bot_response_content if bot_response_content is not None else ""
        bot_response_content = bot_response_content.replace("```html", "").replace("```", "")

    except Exception as e:
        app.logger.error(f"LLM API call failed: {e}")
        # Fallback if LLM call fails, but still log the attempt
        bot_response_content = f"DEV: Echo with history. User said: {user_message}"
        # Optionally, you could return an error to the user here, but the plan suggests a fallback.
        # return jsonify({"error": "Failed to get response from LLM."}), 500
    
    # Ensure bot_response_content is defined (fallback from plan)
    if 'bot_response_content' not in locals() or not bot_response_content: 
         bot_response_content = f"DEV: Echo with history. User said: {user_message}"
    
    # --- Persist Assistant Message ---
    assistant_entry = models.Conversation(
        session_id=session_id_str,
        role='assistant',
        language=language, # Assuming bot replies in the same language
        content=bot_response_content,
        doc_path=match_path_placeholder, # Use actual path from RAG
        similarity=match_score_placeholder # Use actual score from RAG
    )
    db.session.add(assistant_entry)

    # --- Commit to Database (with error handling) ---
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Database commit failed in /api/chat: {e}") # Ensure app.logger is configured or use print
        return jsonify({"error": "Could not save conversation turn."}), 500
    
    # --- Remove old text file logging (commented out as per plan) ---
    # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # match_path  = best_doc['filepath'] if best_doc else "NO_MATCH"
    # match_score = f"{score:.3f}"          if best_doc else "-"
    # with open("questions_log.txt", "a", encoding="utf-8") as log:
    #     log.write(f"{timestamp} | {language.upper()} | {user_message} | "
    #               f"{match_path} | {match_score}\n")

    # --- Return response including session_id ---
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
    app.run(debug=True, port=5000)

# %%
