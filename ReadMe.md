# CreditROBOT

CreditROBOT is a small chatbot application for Creditreform. It uses a Flask backend with SQLAlchemy for database persistence, Flask-Migrate for schema migrations, and the OpenAI API to answer user questions in multiple languages. The system features a session-based memory that maintains a running summary of conversations, allowing for more contextual and coherent interactions. It reads Markdown files from language-specific folders, embeds them using an OpenAI model (e.g., `text-embedding-ada-002`), and retrieves the most relevant document for each query using RAG (Retrieval Augmented Generation). Responses are generated with a powerful LLM (e.g., GPT-4o) and returned to a simple web front end.

## Features
- Multi-lingual support (German, French, Italian, English).
- Retrieval Augmented Generation (RAG) using a knowledge base of Markdown documents.
- Session-based conversational memory with running summaries.
- Database persistence for conversation history and summaries using SQLite.
- Database schema migrations managed by Flask-Migrate.
- Caching for document embeddings to speed up startup.

## Quick start

1. Ensure Python 3.10+ is installed.
2. Clone the repository.
3. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Set the `OPENAI_API_KEY` environment variable with your OpenAI key. You can do this by creating a `.env` file in the `CreditROBOT` directory with the following content:
   ```
   OPENAI_API_KEY='your_openai_api_key_here'
   ```
6. Initialize or upgrade the database (run from within the `CreditROBOT` directory):
   ```bash
   flask db upgrade
   ```
7. Run the backend:
   ```bash
   python app.py
   ```
8. Open `index.html` in your browser and start chatting.

The application automatically scans the language folders at startup, caches embeddings, and stores conversation data in the database. The `questions_log.txt` file is no longer the primary log for conversations.

## Repository layout

- `app.py` – Flask server providing the `/api/chat` route and core application logic.
- `models.py` – Defines SQLAlchemy database models (`Session`, `Conversation`).
- `db.py` – SQLAlchemy database initialization.
- `migrations/` – Directory for Alembic database migration scripts.
- `index.html` – Front‑end page with JavaScript for sending chat messages.
- `Description Deutsch/`, `Description Französisch/`, `Description Italienisch/`, `Description English/` – Source documents for the RAG system.
- `available_models.py` – Helper script to print available OpenAI models.
- `static/` – Images and other static assets used by the front end.
- `.env` – (Should be created by user) For storing environment variables like API keys.
- `.gitignore` – Specifies intentionally untracked files that Git should ignore.
- `requirements.txt` – Lists Python package dependencies.
- `Documentation.md` – Detailed technical documentation.
- `ReadMe.md` – This file.

## Creditreform Services Overview

```mermaid
graph TD
    A[Creditreform Services for Businesses] --> B{Need to Understand Business Partners?};
    B -- Yes --> C[Credit Reports & Monitoring];
    C --> C1[Assess Creditworthiness (Companies & Individuals)];
    C --> C2[Monitor Existing Partners for Changes];
    C --> C3[Check for Compliance (e.g., Anti-Money Laundering)];
    C --> C4[International Reports Available];

    A --> D{Experiencing Unpaid Invoices?};
    D -- Yes --> E[Debt Collection Services];
    E --> E1[Pre-legal & Legal Collection];
    E --> E2[Loss Certificate Management];
    E --> E3[CrediCAP: Collection Insurance for SMEs];

    A --> F{Want to Integrate Risk Checks into Your Systems?};
    F -- Yes --> G[System Integration];
    G --> G1[CrediCONNECT: Link Your ERP/CRM to Creditreform Data];
    G --> G2[RiskCUBE: Secure 'Buy on Account' for Online Shops];
    G --> G3[Automate Debt Collection Processes];

    A --> H{Interested in Ongoing Support & Benefits?};
    H -- Yes --> I[Membership];
    I --> I1[Preferential Rates on Services];
    I --> I2[Access to Shared Payment Experiences];
    I --> I3[Regular Updates & Information];

    C1 --> Z[Make Informed Business Decisions];
    C2 --> Z;
    C3 --> Z;
    E1 --> Y[Improve Cash Flow];
    E2 --> Y;
    G1 --> X[Streamline Operations];
    G2 --> X;
    I1 --> W[Optimize Costs & Security];

    Z --> V[Overall Goal: Minimize Risk & Secure Liquidity];
    Y --> V;
    X --> V;
    W --> V;
```
