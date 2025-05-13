#%%
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from datetime import datetime
from openai import OpenAI

app = Flask(__name__)
CORS(app)

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
        ("Description Italienisch", "it"),
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
                # Compute embedding
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
DU MUSST IMMER ALLE LINKS AUSGEBEN
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
YOU MUST ALWAYS OUTPUT *ALL* LINKS  
KEEP IT SHORT  
IF YOU ARE NOT SURE ABOUT YOUR ANSWER, REFER TO THE CONTACT FORM:  
https://www.creditreform.ch/creditreform/kontakt
"""
    else:
        # fallback if unknown
        return "Please answer in HTML."

########################################################
# 2) FLASK ROUTES
########################################################

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json or {}
        user_message = data.get('message', '').strip()
        language = data.get('lang', 'de').lower()[:2]  # 'de','fr','it', etc.

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Retrieve best doc for the user query
        best_doc, score = retrieve_best_doc(user_message, user_lang=language)

        # Log the question and the match
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        match_path  = best_doc['filepath'] if best_doc else "NO_MATCH"
        match_score = f"{score:.3f}"          if best_doc else "-"
        with open("questions_log.txt", "a", encoding="utf-8") as log:
            log.write(f"{timestamp} | {language.upper()} | {user_message} | "
                      f"{match_path} | {match_score}\n")
        if not best_doc:
            # fallback: no doc found or the folder was empty
            system_prompt = load_base_prompt(language)
            system_prompt += "\n\n(Keine passenden Dokumente gefunden.)\n"
        else:
            print(f"Best match: {best_doc['filepath']} (score={score:.3f})")
            # Build final system prompt
            base_prompt = load_base_prompt(language)
            final_prompt = load_final_prompt(language)
            system_prompt = (
                f"{base_prompt}\n\n"                
                f"{best_doc['content']}\n"
                f"---\n"
                f"{final_prompt}\n"
            )

        # Call GPT with the system prompt + user message
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.0
        )

        bot_response = response.choices[0].message.content
        # Strip triple backticks if the model includes code fences
        bot_response = bot_response.replace("```html", "").replace("```", "")

        return jsonify({'response': bot_response})

    except Exception as e:
        print("Error in /api/chat:", str(e))
        return jsonify({'error': str(e)}), 500

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
