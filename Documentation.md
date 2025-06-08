# Project Documentation

This document provides a detailed technical explanation of how the CreditROBOT chatbot works, its architecture, and how to run it in development.

## 1. Overview

CreditROBOT is a multi-lingual chatbot designed to provide information about Creditreform services. It leverages a Flask-based backend API, OpenAI's language models (for embeddings, summarization, and response generation), and a SQLite database for persistent conversation memory.

The core functionality revolves around a Retrieval Augmented Generation (RAG) pattern combined with a sophisticated session memory system. At startup, the application processes a knowledge base of Markdown documents (organized by language in `Description*` folders), computes text embeddings for their content using an OpenAI model (e.g., `text-embedding-ada-002`), and caches these embeddings in `embeddings_cache.pkl` to accelerate subsequent startups.

When a user interacts with the chatbot via the `index.html` frontend, their message is sent to the `/api/chat` endpoint. The backend then performs the following key operations:
1.  **Session Management**: Identifies or creates a unique conversation session for the user. Each session maintains a running summary of the dialogue, stored in the database.
2.  **Message Persistence**: Stores the user's message in the `conversations` table in the database.
3.  **Information Retrieval (RAG)**: Embeds the user's query and compares it against the pre-computed document embeddings using cosine similarity to find the most relevant document from the knowledge base.
4.  **Prompt Engineering**: Constructs a detailed prompt for the main language model (e.g., `gpt-4o`). This prompt includes:
    *   System instructions defining the chatbot's role and response format (HTML).
    *   The current running summary of the conversation (retrieved from the `sessions` table).
    *   The content of the most relevant document found via RAG.
    *   The user's current message.
5.  **Response Generation**: Sends the engineered prompt to the main LLM to generate a contextually relevant and factually grounded response.
6.  **Response Persistence**: Stores the assistant's response in the `conversations` table.
7.  **Memory Update**: Uses a secondary, faster LLM (e.g., `gpt-4o-mini`) to update the running `conversation_summary` for the session in the `sessions` table, incorporating the latest user message and assistant response.
8.  **Transaction Commit**: Commits all database changes (new messages, updated summary) atomically.
9.  **Response Delivery**: Sends the generated HTML response back to the frontend.

This architecture ensures that the chatbot can handle long conversations effectively by relying on a concise summary rather than the full transcript for context, while still grounding its responses in the provided knowledge base.

## 2. Detailed Workflow: Chat Request Lifecycle

The following steps outline the process from when a user sends a message to when they receive a response:

1.  **Frontend Request (`index.html`)**:
    *   The user types a message into the input field and selects a language from the dropdown.
    *   Client-side JavaScript captures the message, selected language, and the current `sessionId` (if one exists from a previous interaction; initially null).
    *   An asynchronous POST request is made to the `/api/chat` endpoint of the Flask backend.
    *   The request payload is a JSON object: `{"message": "User's query", "lang": "de", "sessionId": "optional-uuid-string"}`.

2.  **API Endpoint Reception (`/api/chat` in `app.py`)**:
    *   The Flask route `@app.route('/api/chat', methods=['POST'])` handles the incoming request.
    *   `request.get_json()` parses the JSON payload.
    *   The `sessionId` is retrieved; if it's not provided or is null/empty, a new `uuid.uuid4()` is generated to uniquely identify the new conversation session.
    *   The `user_message` and `language` are extracted.
    *   A basic check ensures `user_message` is not empty; if so, a 400 error is returned.

3.  **Session Initialization/Retrieval (`get_or_create_session` function)**:
    *   The `session_id_str` (either from the client or newly generated) is passed to `get_or_create_session(session_id_str)`.
    *   This function queries the `sessions` table: `db.session.query(models.Session).filter_by(session_id=session_id_str).first()`.
    *   **If a session exists**: The corresponding `Session` SQLAlchemy object is returned. This object contains the `id`, `session_id`, `created_at`, `updated_at`, and crucially, the `conversation_summary`.
    *   **If no session exists**:
        *   A new `models.Session` object is instantiated: `session = models.Session(session_id=session_id_str)`. The `__init__` method in the `Session` class handles setting the `session_id`. Other fields like `created_at`, `updated_at`, and the default `conversation_summary` ("The conversation has just begun.") are set by SQLAlchemy based on column defaults.
        *   The new `session` object is added to the database session: `db.session.add(session)`.
        *   An immediate `db.session.commit()` is performed. This is important so that the new `Session` record is persisted and has its primary key (`id`) populated, making it available for foreign key relationships with `Conversation` entries within the same overall transaction.
    *   The function returns the (either fetched or newly created) `Session` object.

4.  **User Message Persistence (Pre-Commit Stage)**:
    *   A `models.Conversation` object is created to represent the user's turn:
        `user_entry = models.Conversation(session_uuid=session.session_id, role='user', language=language, content=user_message)`
        Note: `session.session_id` (the UUID string) is used for `session_uuid` to link to the `sessions` table.
    *   This `user_entry` is added to the current SQLAlchemy database session: `db.session.add(user_entry)`. It is not yet written to the database; it's pending the final commit.

5.  **Retrieval Augmented Generation (RAG) (`retrieve_best_doc` function)**:
    *   The `user_message` and `user_lang` are passed to `retrieve_best_doc`.
    *   `compute_embedding(user_message)` is called, which in turn calls the OpenAI embeddings API (e.g., `text-embedding-ada-002`) to get a vector representation of the user's query.
    *   The function iterates through the globally loaded `DOCS` list (which contains pre-embedded knowledge base documents, filtered by `user_lang`).
    *   `cosine_similarity(query_emb, doc["embedding"])` calculates the similarity between the user query embedding and each document embedding.
    *   The document with the highest similarity score (above a certain threshold, implicitly) is selected as `best_doc`.
    *   Returns `best_doc` (a dictionary containing filepath, content, etc.) and `score`.

6.  **Prompt Construction for Main LLM**:
    *   `load_base_prompt(language)` and `load_final_prompt(language)` fetch language-specific instruction templates.
    *   `contextual_history = f"CONTEXT FROM PREVIOUSLY IN THE CONVERSATION:\n{session.conversation_summary}"` incorporates the current state of the conversation summary.
    *   The final `system_prompt` is assembled by combining these elements with the content of `best_doc['content']` (if found). This prompt provides the LLM with its role, formatting instructions, conversational context, relevant knowledge, and the user's immediate query implicitly through the message list.

7.  **Main LLM Call (OpenAI API for Response Generation)**:
    *   `client.chat.completions.create()` is called with:
        *   `model="gpt-4o"` (or another powerful model).
        *   `messages`: A list containing two items:
            1.  `ChatCompletionSystemMessageParam(role="system", content=system_prompt)`
            2.  `ChatCompletionUserMessageParam(role="user", content=user_message)`
        *   `max_tokens` (e.g., 700) to limit response length.
        *   `temperature=0.0` for deterministic, factual responses.
    *   The response content is extracted from `llm_api_response.choices[0].message.content`.
    *   Any "```html" or "```" markers are stripped from the response.
    *   If an API error occurs, a generic error message is set as `bot_response_content`.

8.  **Assistant Response Persistence (Pre-Commit Stage)**:
    *   A `models.Conversation` object is created for the assistant's response:
        `assistant_entry = models.Conversation(session_uuid=session.session_id, role='assistant', language=language, content=bot_response_content, doc_path=best_doc['filepath'] if best_doc else None, similarity=score if best_doc else None)`
    *   This `assistant_entry` is added to the SQLAlchemy database session: `db.session.add(assistant_entry)`.

9.  **Conversation Summary Update (`update_conversation_summary` function)**:
    *   The current `session` object, `user_message`, and `bot_response_content` are passed to this function.
    *   It retrieves `current_summary = session.conversation_summary`.
    *   A `summarizer_prompt` is constructed, instructing a model to update the `current_summary` based on the `LATEST INTERACTION` (user message + assistant response).
    *   Another call to `client.chat.completions.create()` is made, this time using a faster, cheaper model (e.g., `"gpt-4o-mini"`), with the `summarizer_prompt`. Temperature is low (0.2) for factual summarization, and `max_tokens` is limited (e.g., 250).
    *   The `new_summary` from this LLM call updates the `session.conversation_summary` attribute of the in-memory `Session` object. This change will be part of the upcoming database commit.
    *   If the summarization API call fails, an error is logged, but the application continues using the previous summary; the `session.conversation_summary` remains unchanged.

10. **Database Commit (Transaction Finalization)**:
    *   `db.session.commit()` is called. This attempts to write all accumulated changes in the current SQLAlchemy session to the database in a single atomic transaction. This includes:
        *   The new user `Conversation` record.
        *   The new assistant `Conversation` record.
        *   The updated `conversation_summary` field in the existing `Session` record.
    *   **If successful**: All data is durably stored.
    *   **If an error occurs during commit**: `db.session.rollback()` is called to discard the changes from this transaction, preventing partial updates. An error is logged, and a 500 HTTP error is returned to the client.

11. **Response to Frontend**:
    *   A JSON object `{'response': bot_response_content, 'sessionId': session_id_str}` is returned to the client with a 200 OK status.
    *   The frontend JavaScript receives this JSON, updates its `sessionId` variable for future requests in the same session, and renders the HTML `response` in the chat window.

## 3. Database and Migrations

The application uses a SQLite database (managed by SQLAlchemy and Flask-Migrate) to store conversation data.

-   **`models.py`**: Defines the database schema.
    -   `Session` model: Stores session-specific data, including a unique `session_id` (UUID string, primary identifier for a conversation) and a `conversation_summary` (Text) which is a running summary of the dialogue. It also has an auto-incrementing integer `id` as its primary key, and `created_at`/`updated_at` timestamps.
    -   `Conversation` model: Stores individual turns (user messages and assistant responses). Each turn is linked to a `Session` via a `session_uuid` foreign key (which references `sessions.session_id`). Each turn includes `role` ('user' or 'assistant'), `language`, `content`, `timestamp`, and optionally, `doc_path` and `similarity` if a document was retrieved for that turn.
-   **`db.py`**: Initializes the SQLAlchemy `db` object (`db = SQLAlchemy()`), which is then associated with the Flask app in `app.py` (`db.init_app(app)`).
-   **`migrations/` directory**: Contains Alembic migration scripts. These scripts track changes to the database schema (defined in `models.py`) and allow for incremental updates to the database structure.
    -   To apply migrations (e.g., after a schema change in `models.py` or when setting up the project for the first time):
        ```bash
        # Navigate to the CreditROBOT directory if you are not already there
        cd CreditROBOT 
        flask db upgrade
        ```
        This command applies any pending migrations to bring the database schema to the latest version.
    -   To generate a new migration after changing `models.py`:
        ```bash
        flask db migrate -m "Descriptive message for your migration"
        # Review the generated script in migrations/versions/
        flask db upgrade
        ```

## 4. Key Modules and Components

-   **`app.py` – Main Flask Application Server**:
    *   **Initialization**: Sets up Flask, CORS, SQLAlchemy, Flask-Migrate, and the OpenAI client. Loads environment variables from `.env`.
    *   **`scan_language_folders()`**: Called at startup.
        *   Iterates through language-specific subdirectories (e.g., `Description Deutsch`).
        *   Reads content from `.md` files.
        *   Manages a cache (`embeddings_cache.pkl`) for document embeddings. If a document hasn't changed (based on modification time), its cached embedding is used. Otherwise, a new embedding is computed via `compute_embedding`.
        *   Stores document content, metadata, and embeddings in the global `DOCS` list.
    *   **`compute_embedding(text, model)`**: Helper function to get text embeddings from OpenAI.
    *   **`cosine_similarity(a, b)`**: Helper function to calculate cosine similarity between two vectors.
    *   **`retrieve_best_doc(user_query, user_lang)`**: Implements the retrieval part of RAG.
    *   **`load_base_prompt(language)` & `load_final_prompt(language)`**: Return language-specific prompt templates.
    *   **`get_or_create_session(session_id)`**: Manages session persistence (described in Lifecycle).
    *   **`update_conversation_summary(session, user_message, assistant_message)`**: Updates the conversation summary (described in Lifecycle).
    *   **`/api/chat` Endpoint**: The main interaction point (described in Lifecycle).
    *   **`/` Endpoint**: Serves the `index.html` frontend.
-   **`models.py` – Database Models**: Defines the structure of the `sessions` and `conversations` tables using SQLAlchemy ORM classes.
-   **`db.py` – Database Setup**: Provides the shared `SQLAlchemy` instance.
-   **`index.html` – Frontend**: A simple HTML page with JavaScript to:
    *   Send user messages and language preference to the `/api/chat` endpoint.
    *   Receive and display the HTML response from the chatbot.
    *   Store and reuse the `sessionId` to maintain conversation context across multiple requests.
-   **`Description*` Folders**: Contain the Markdown documents forming the knowledge base for RAG.
-   **`requirements.txt`**: Lists Python dependencies.
-   **`.env` (User-created)**: Stores sensitive information like `OPENAI_API_KEY`.
-   **`.gitignore`**: Specifies files and directories to be ignored by Git (e.g., `venv/`, `__pycache__/`, `instance/`, `.env`, `embeddings_cache.pkl`).
-   **`embeddings_cache.pkl`**: Stores pre-computed embeddings of the knowledge base documents to speed up application startup. It is gitignored.
-   **`instance/creditrobot.db`**: The SQLite database file. It is gitignored.

The `questions_log.txt` file is no longer used for detailed conversation logging as this is now handled by the database. It might still be present for basic, high-level query logging if desired, but the primary store for conversation history and state is the database.

## 5. Running the Application

1.  **Prerequisites**:
    *   Python 3.10 or later.
    *   Git (for cloning the repository).
2.  **Setup**:
    *   Clone the repository.
    *   Navigate to the `CreditROBOT` project directory.
    *   Create and activate a Python virtual environment:
        ```bash
        python -m venv venv
        source venv/bin/activate  # For Linux/macOS
        # venv\Scripts\activate    # For Windows
        ```
    *   Install dependencies:
        ```bash
        pip install -r requirements.txt
        ```
    *   Create a `.env` file in the `CreditROBOT` directory and add your OpenAI API key:
        ```
        OPENAI_API_KEY='your_actual_openai_api_key'
        ```
3.  **Database Initialization**:
    *   Run from within the `CreditROBOT` directory:
        ```bash
        flask db upgrade
        ```
        This command creates the database and applies all migrations if it's the first time, or applies any pending migrations if the database already exists.
4.  **Start the Server**:
    *   Run from within the `CreditROBOT` directory:
        ```bash
        python app.py
        ```
        The Flask development server will typically start on `http://localhost:5000`.
5.  **Access the Chatbot**:
    *   Open `index.html` (located in the `CreditROBOT` directory) in a web browser.

## 6. Notes and Best Practices

-   **Knowledge Base**: Documents in the `Description*` folders can be edited or replaced. They must be Markdown files (`.md`). After changes, restart the application to re-scan and re-embed (or rely on the caching mechanism to update changed files).
-   **Database**: Conversation history (individual turns and running summaries) is stored in the SQLite database (`instance/creditrobot.db` by default). This file is gitignored.
-   **Embedding Cache**: The `embeddings_cache.pkl` file speeds up startup. It's safe to delete; it will be regenerated on the next run.
-   **Error Logging**: The Flask application uses `app.logger` for logging errors and informational messages, which will typically output to the console where the server is running.
-   **Security**: The `.env` file containing the API key should never be committed to version control. The `.gitignore` file is configured to prevent this.
-   **Development vs. Production**: The current setup uses the Flask development server. For production, a more robust WSGI server (like Gunicorn or uWSGI) behind a reverse proxy (like Nginx) would be recommended. Database choice might also change for production (e.g., PostgreSQL).

## 7. Project Architecture Diagram

```mermaid
graph TD
    A[User] -- HTTP Request (Message, Lang, SessionID) --> B{Flask Application};

    subgraph Flask Application
        direction LR
        B1["index.html Frontend"] -. Serves UI .-> A;
        B -- Routes to --> B2["/api/chat Endpoint"];
        B2 -- Gets/Creates Session --> DB[(SQLite Database)];
        B2 -- Logs User Message --> DB_Conv[Conversations Table];
        B2 -- Embed User Query --> OpenAI_Emb[OpenAI API Embeddings];
        B2 -- Retrieves Docs --> KB[Knowledge Base (.md files)];
        KB -- Scans & Embeds (on startup/update) --> OpenAI_Emb;
        KB -- Stores/Retrieves Embeddings --> Cache[embeddings_cache.pkl];
        B2 -- Constructs Prompt --> OpenAI_Chat[OpenAI API Chat Completions];
        OpenAI_Chat -- HTML Response --> B2;
        B2 -- Logs Assistant Response --> DB_Conv;
        B2 -- Updates Summary (via OpenAI_Chat_Mini) --> DB_Sess[Sessions Table];
        B2 -- HTTP Response (HTML) --> B1;
    end

    subgraph Database
        direction TB
        DB_Sess[Sessions Table];
        DB_Conv[Conversations Table];
    end

    subgraph OpenAI Services
        direction TB
        OpenAI_Emb;
        OpenAI_Chat;
        OpenAI_Chat_Mini[OpenAI API Chat (Summarization)];
    end

    DB -- Contains --> DB_Sess;
    DB -- Contains --> DB_Conv;
    B2 -- Uses for RAG Context --> Cache;
    B2 -- Uses for Summarization --> OpenAI_Chat_Mini;

    style A fill:#f9f,stroke:#333,stroke-width:2px;
    style KB fill:#ccf,stroke:#333,stroke-width:2px;
    style DB fill:#fcc,stroke:#333,stroke-width:2px;
    style Cache fill:#lightgrey,stroke:#333,stroke-width:1px;
```

## Diagram Explanation

This diagram illustrates the architecture of the CreditRobot application. The main components and flow are as follows:

1.  **User Interaction**: The User interacts with the application through the `index.html` frontend. Messages, selected language, and a session ID are sent to the Flask backend.
2.  **Flask Application (Backend)**:
    *   The `/api/chat` endpoint processes the user's request.
    *   It manages user sessions and conversation history stored in an **SQLite Database**. The database has two main tables: `Sessions` (for session data and conversation summaries) and `Conversations` (for individual messages).
    *   **Knowledge Base Retrieval (RAG)**:
        *   The application scans `.md` files from language-specific folders (`Description Deutsch/`, `Description English/`, etc.) to build its knowledge base.
        *   Text from these files is embedded using the **OpenAI Embeddings API**. These embeddings are cached in `embeddings_cache.pkl` for efficiency.
        *   When a user sends a message, it's embedded, and the most relevant document from the knowledge base is retrieved by comparing embeddings.
    *   **OpenAI Chat Completions**:
        *   A detailed prompt is constructed using the system role, conversation summary (from the `Sessions` table), the content of the retrieved document, and the current user message.
        *   This prompt is sent to the **OpenAI Chat API** (e.g., gpt-4.1) to generate a response.
        *   A separate, faster OpenAI model (e.g., gpt-4.1-mini) is used to update the conversation summary after each turn.
    *   The generated HTML response is logged and sent back to the user.
3.  **OpenAI Services**: The application relies on OpenAI for text embeddings and chat message generation/summarization.
4.  **Database**: Stores session information, conversation history, and summaries.
5.  **Knowledge Base & Cache**: Markdown files form the core information source, and their embeddings are cached to speed up retrieval.

The diagram shows the flow of data from the user's request through the backend processing, interaction with OpenAI and the database, and finally the response back to the user.
