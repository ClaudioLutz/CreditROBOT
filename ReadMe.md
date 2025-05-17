# CreditROBOT

CreditROBOT is a small chatbot application for Creditreform. It uses a Flask backend together with the OpenAI API to answer user questions in multiple languages. The system reads Markdown files from the language folders, embeds them with `text-embedding-ada-002` and retrieves the most relevant document for each query. Responses are generated with GPT and returned to a simple web front end.

## Quick start

1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
2. Set the `OPENAI_API_KEY` environment variable with your OpenAI key.
3. Run the backend:
   ```bash
   python app.py
   ```
4. Open `index.html` in your browser and start chatting.

The script automatically scans the language folders at startup and logs each question to `questions_log.txt`.

## Repository layout

- `app.py` – Flask server providing the `/api/chat` route.
- `index.html` – front‑end page with JavaScript for sending chat messages.
- `Description Deutsch`, `Description Französisch`, `Description Italienisch`, `Description English` – source documents in different languages.
- `available_models.py` – helper script to print the available OpenAI models.
- `static/` – images used by the front end.


