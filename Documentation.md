# Project Documentation

This document provides additional details on how the CreditROBOT chatbot works and how to run it in development.

## Overview

The application combines a Flask API with OpenAI services to deliver answers about Creditreform in multiple languages. Text documents in German, French, Italian and English are stored in the respective `Description*` folders. They are embedded at startup using the OpenAI embedding model. When a user sends a question via the `/api/chat` endpoint, the backend retrieves the most similar document using cosine similarity and composes a prompt for GPT-4.

## Important modules

- `app.py` – Main Flask server. Key functions:
  - `scan_language_folders()` reads all Markdown files under the language folders and stores their embeddings in memory.
  - `retrieve_best_doc()` computes cosine similarity between the user query and the embedded documents to pick the best match.
  - `load_base_prompt()` and `load_final_prompt()` provide language-specific prompts used to frame the GPT request.
  - `/api/chat` endpoint accepts a JSON payload with `message` and `lang` fields and returns the generated HTML response.
- `available_models.py` – Small script that lists all OpenAI models for the configured API key.

All questions are appended to `questions_log.txt` with the timestamp, language and matched document path.

## Running the application

1. Ensure Python 3.10 or later is installed.
2. Install dependencies with `pip install -r requirements.txt`.
3. Export your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=YOUR_KEY
   ```
4. Start the server:
   ```bash
   python app.py
   ```
5. Open `index.html` in a browser to use the chatbot. The page includes a language selector and communicates with the API at `http://localhost:5000/api/chat`.

## Notes

- The documents in the language folders can be edited or replaced. They must be Markdown files (`.md`).
- The backend logs queries to `questions_log.txt` for future reference.
- Images for the interface are stored in the `static/` directory.


