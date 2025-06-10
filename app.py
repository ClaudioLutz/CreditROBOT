#%%
import os
import uuid # Added
import pickle # Added for caching
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
                    "embedding": embedding,
                    "char_count": len(text_content)  # Added char_count
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

def retrieve_relevant_docs(user_query, user_lang=None, top_n=5, max_total_chars=8000):
    """
    1) Embeds user_query.
    2) Optionally filters DOCS by user_lang.
    3) Calculates cosine similarity to each doc.
    4) Sorts docs by similarity.
    5) Selects docs based on top_n and max_total_chars constraints.
    6) Returns a list of selected documents, each including its score.
    """
    query_emb = compute_embedding(user_query)

    docs_with_scores = []
    for doc in DOCS:
        if user_lang and (doc["language"] != user_lang):
            continue
        
        # Ensure doc has 'embedding' and 'char_count'
        if "embedding" not in doc or "char_count" not in doc:
            print(f"[WARN] Document {doc.get('filepath', 'Unknown')} is missing 'embedding' or 'char_count'. Skipping.")
            continue

        score = cosine_similarity(query_emb, doc["embedding"])
        docs_with_scores.append({
            **doc,  # Unpack all existing doc info (filepath, content, char_count, etc.)
            "score": score
        })
        
    # Sort by score descending
    docs_with_scores.sort(key=lambda x: x["score"], reverse=True)
    
    selected_docs = []
    current_total_chars = 0
    
    for doc_with_score in docs_with_scores:
        if len(selected_docs) >= top_n:
            break  # Reached max number of documents

        # Check if adding this document would exceed the character limit
        if (current_total_chars + doc_with_score['char_count']) <= max_total_chars:
            selected_docs.append(doc_with_score)
            current_total_chars += doc_with_score['char_count']
        # If it doesn't fit, we skip it and try the next one,
        # as a less similar but smaller document might still fit.
            
    return selected_docs

def load_base_prompt(language='de'):
    """Return a short system prompt in the user's language with instructions on context usage."""
    if language == 'de':
        return """
Antworte auf Deutsch.

**Rolle:**
Du bist ein hochspezialisierter Assistent der Creditreform. Deine Aufgabe ist es, präzise und kompetente Antworten zu liefern.

**Kontext-Anleitung:**
Du erhältst unten möglicherweise zwei separate Kontextabschnitte:
1.  `ZUSAMMENFASSUNG DES BISHERIGEN GESPRÄCHS`: Dies ist eine Zusammenfassung eurer vorherigen Interaktionen.
2.  `RELEVANTE INFORMATIONEN AUS WISSENSDOKUMENTEN`: Dies sind Auszüge aus Wissensartikeln, die für die aktuelle Anfrage relevant sein könnten.

**WIE DU ANTWORTEN SOLLST:**
-   Wenn der Nutzer explizit nach dem bisherigen Gesprächsverlauf fragt (z.B. "Worüber haben wir gesprochen?", "Was war meine letzte Frage?"), dann antworte **primär** basierend auf der `ZUSAMMENFASSUNG DES BISHERIGEN GESPRÄCHS`. Die Wissensdokumente sollten in diesem Fall eine untergeordnete Rolle spielen oder ignoriert werden, es sei denn, sie sind direkt Teil der erinnerten Konversation.
-   Für alle anderen Fachfragen oder allgemeinen Anfragen, nutze primär die `RELEVANTE INFORMATIONEN AUS WISSENSDOKUMENTEN`, um deine Antwort zu formulieren. Die Gesprächszusammenfassung kann dir helfen, den breiteren Kontext der Nutzeranliegen zu verstehen, aber die Fakten für die Antwort sollten hauptsächlich aus den Wissensdokumenten stammen.
"""
    elif language == 'fr':
        return """
Réponds en français.

**Rôle :**
Tu es un assistant hautement spécialisé de Creditreform. Ta tâche est de fournir des réponses précises et compétentes.

**Instructions sur le contexte :**
Tu pourrais recevoir ci-dessous deux sections de contexte distinctes :
1.  `RÉSUMÉ DE LA CONVERSATION PRÉCÉDENTE` : Ceci est un résumé de vos interactions précédentes.
2.  `INFORMATIONS PERTINENTES DES DOCUMENTS DE CONNAISSANCE` : Ce sont des extraits d'articles de connaissance qui pourraient être pertinents pour la requête actuelle.

**COMMENT RÉPONDRE :**
-   Si l'utilisateur demande explicitement le déroulement de la conversation précédente (par exemple, "De quoi avons-nous parlé ?", "Quelle était ma dernière question ?"), réponds **principalement** en te basant sur le `RÉSUMÉ DE LA CONVERSATION PRÉCÉDENTE`. Les documents de connaissance devraient jouer un rôle secondaire dans ce cas ou être ignorés, à moins qu'ils ne fassent directement partie de la conversation mémorisée.
-   Pour toutes les autres questions techniques ou générales, utilise principalement les `INFORMATIONS PERTINENTES DES DOCUMENTS DE CONNAISSANCE` pour formuler ta réponse. Le résumé de la conversation peut t'aider à comprendre le contexte plus large des préoccupations de l'utilisateur, mais les faits pour la réponse devraient provenir principalement des documents de connaissance.
"""
    elif language == 'it':
        return """
Rispondi in italiano.

**Ruolo:**
Sei un assistente altamente specializzato di Creditreform. Il tuo compito è fornire risposte precise ed esperte.

**Istruzioni sul contesto:**
Potresti ricevere di seguito due sezioni di contesto separate:
1.  `RIASSUNTO DELLA CONVERSAZIONE PRECEDENTE`: Questo è un riassunto delle vostre interazioni precedenti.
2.  `INFORMAZIONI RILEVANTI DAI DOCUMENTI DI CONOSCENZA`: Questi sono estratti da articoli di conoscenza che potrebbero essere rilevanti per la richiesta attuale.

**COME RISPONDERE:**
-   Se l'utente chiede esplicitamente dello storico della conversazione precedente (ad esempio, "Di cosa abbiamo parlato?", "Qual è stata la mia ultima domanda?"), rispondi **principalmente** basandoti sul `RIASSUNTO DELLA CONVERSAZIONE PRECEDENTE`. I documenti di conoscenza dovrebbero avere un ruolo secondario in questo caso o essere ignorati, a meno che non facciano direttamente parte della conversazione memorizzata.
-   Per tutte le altre domande tecniche o generali, utilizza principalmente le `INFORMAZIONI RILEVANTI DAI DOCUMENTI DI CONOSCENZA` per formulare la tua risposta. Il riassunto della conversazione può aiutarti a comprendere il contesto più ampio delle preoccupazioni dell'utente, ma i fatti per la risposta dovrebbero provenire principalmente dai documenti di conoscenza.
"""
    elif language == 'en':
        return """
Respond in English.

**Role:**
You are a highly-specialised Creditreform assistant. Your task is to provide precise and expert answers.

**Context Instructions:**
You may receive two separate context sections below:
1.  `SUMMARY OF THE PREVIOUS CONVERSATION`: This is a summary of your previous interactions.
2.  `RELEVANT INFORMATION FROM KNOWLEDGE DOCUMENTS`: These are excerpts from knowledge articles that might be relevant to the current query.

**HOW YOU SHOULD RESPOND:**
-   If the user explicitly asks about the previous course of the conversation (e.g., "What did we talk about?", "What was my last question?"), then respond **primarily** based on the `SUMMARY OF THE PREVIOUS CONVERSATION`. The knowledge documents should play a secondary role in this case or be ignored, unless they are directly part of the remembered conversation.
-   For all other technical or general inquiries, primarily use the `RELEVANT INFORMATION FROM KNOWLEDGE DOCUMENTS` to formulate your answer. The conversation summary can help you understand the broader context of the user's concerns, but the facts for the answer should mainly come from the knowledge documents.
"""
    else:
        # fallback if unknown
        return "You are a Creditreform assistant. Please answer in HTML. You may receive context from conversation history or documents."
    

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
    
    # Use a placeholder if the current summary is None or empty
    current_summary_for_prompt = session.conversation_summary if session.conversation_summary and session.conversation_summary.strip() else "(No previous summary)"
    
    # This is a highly specific prompt for the summarization task
    summarizer_prompt = f"""
    Your task is to update a conversation summary. You will be given the previous summary
    and the latest user-assistant interaction. Integrate the new information from the interaction
    into the summary concisely. Preserve key details, names, topics, and user goals.
    The user is asking about Creditreform.

    PREVIOUS SUMMARY:
    "{current_summary_for_prompt}"

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
        # Fallback to the original session.conversation_summary if new_summary is empty
        session.conversation_summary = new_summary.strip() if new_summary and new_summary.strip() else session.conversation_summary
        # The calling function will be responsible for the final db.session.commit()
        
    except Exception as e:
        app.logger.error(f"Failed to update conversation summary for session {session.session_id}: {e}")
        # If summarization fails, we don't crash. The old summary will be used next time.

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

    # 1. Get or create the session object
    session = get_or_create_session(session_id_str)

    # 2. Persist the user message turn (but don't commit yet)
    user_entry = models.Conversation(session_uuid=session.session_id, role='user', language=language, content=user_message)
    db.session.add(user_entry)

    # 3. Perform RAG retrieval
    # Retrieve top N relevant documents, considering character limits
    retrieved_docs = retrieve_relevant_docs(user_message, user_lang=language, top_n=3, max_total_chars=5000)

    # 4. Construct the main prompt using the SUMMARY, and new multi-doc context
    base_prompt = load_base_prompt(language)
    final_prompt = load_final_prompt(language)
    
    # Define language-specific headings for context sections
    summary_heading = {
        'de': "ZUSAMMENFASSUNG DES BISHERIGEN GESPRÄCHS",
        'fr': "RÉSUMÉ DE LA CONVERSATION PRÉCÉDENTE",
        'it': "RIASSUNTO DELLA CONVERSAZIONE PRECEDENTE",
        'en': "SUMMARY OF THE PREVIOUS CONVERSATION"
    }.get(language, "SUMMARY OF THE PREVIOUS CONVERSATION")

    kb_heading = {
        'de': "RELEVANTE INFORMATIONEN AUS WISSENSDOKUMENTEN",
        'fr': "INFORMATIONS PERTINENTES DES DOCUMENTS DE CONNAISSANCE",
        'it': "INFORMAZIONI RILEVANTI DAI DOCUMENTI DI CONOSCENZA",
        'en': "RELEVANT INFORMATION FROM KNOWLEDGE DOCUMENTS"
    }.get(language, "RELEVANT INFORMATION FROM KNOWLEDGE DOCUMENTS")

    # Inject the conversation summary into the prompt
    if session.conversation_summary and session.conversation_summary.strip():
        contextual_history_content = session.conversation_summary
    else:
        contextual_history_content = "(No summary yet for this session.)"
    contextual_history = f"{summary_heading}:\n{contextual_history_content}"
    
    knowledge_base_section = ""
    if retrieved_docs:
        knowledge_base_content = ""
        for doc in retrieved_docs:
            knowledge_base_content += f"---\nSource: {doc['filepath']}\nContent:\n{doc['content']}\n"
        # Remove the last "---" if it exists and add a final one or ensure proper formatting
        if knowledge_base_content.endswith("---\n"):
             knowledge_base_content = knowledge_base_content[:-4] # remove last "---" + newline
        knowledge_base_content += "---" # Add a final separator
        knowledge_base_section = f"\n{kb_heading}:\n{knowledge_base_content}\n"
    else:
        knowledge_base_section = f"\n{kb_heading}:\n(No matching document found.)\n---\n"
        
    system_prompt = (
        f"{base_prompt}\n\n"
        f"{contextual_history}\n" # Removed extra \n as kb_section will add one if present
        f"{knowledge_base_section}\n" 
        f"{final_prompt}\n"
    )

    # 5. Call the main LLM (gpt-4.1) with only the current user message
    try:
        llm_api_response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                ChatCompletionSystemMessageParam(role="system", content=system_prompt),
                ChatCompletionUserMessageParam(role="user", content=user_message)
            ],
            max_tokens=700,
            temperature=0.0
        )
        bot_response_content = llm_api_response.choices[0].message.content or ""
        bot_response_content = bot_response_content.replace("```html", "").replace("```", "")
    except Exception as e:
        app.logger.error(f"LLM API call failed: {e}")
        bot_response_content = "I am sorry, but I encountered an error. Please try again."
    
    # 6. Persist the assistant message turn (don't commit yet)
    # Determine doc_path and similarity for logging (using the top document from retrieved_docs)
    log_doc_path = retrieved_docs[0]['filepath'] if retrieved_docs else None
    log_similarity = retrieved_docs[0]['score'] if retrieved_docs else None

    assistant_entry = models.Conversation(
        session_uuid=session.session_id,
        role='assistant',
        language=language,
        content=bot_response_content,
        doc_path=log_doc_path,
        similarity=log_similarity
    )
    db.session.add(assistant_entry)

    # 7. IMPORTANT: Update the conversation summary
    update_conversation_summary(session, user_message, bot_response_content)

    # 8. Commit the entire transaction (new turns, updated summary)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Database commit failed: {e}")
        return jsonify({"error": "Could not save conversation."}), 500

    # 9. Return the response to the user
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
