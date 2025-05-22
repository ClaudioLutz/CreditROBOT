# CreditROBOT

CreditROBOT is a small chatbot application for Creditreform. It uses a Flask backend together with the OpenAI API to answer user questions in multiple languages. The system reads Markdown files from the language folders, embeds them with `text-embedding-ada-002` and retrieves the most relevant document for each query. Responses are generated with GPT and returned to a simple web front end.

## Quick start

1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
2. Set the `OPENAI_API_KEY` environment variable with your OpenAI key. (See Configuration section below for more details on using a `.env` file).
3. Run the backend:
   ```bash
   python app.py
   ```
4. Open `index.html` in your browser and start chatting.

The script automatically scans the language folders at startup and logs each question to `questions_log.txt`.

## Configuration

This application requires an OpenAI API key and allows for optional configuration of the OpenAI models used.

### Environment Variables

The application uses the following environment variables:

*   **`OPENAI_API_KEY`** (required): Your OpenAI API key. This must be set for the application to function.
*   **`EMBEDDING_MODEL`** (optional): Specifies the OpenAI model to use for creating text embeddings.
    *   Defaults to `"text-embedding-ada-002"` if not set.
*   **`CHAT_MODEL`** (optional): Specifies the OpenAI model to use for generating chat responses.
    *   Defaults to `"gpt-4o"` if not set.

### Using a `.env` File

For convenience, especially during development, you can manage these environment variables using a `.env` file:

1.  **Create a `.env` file:** Copy the provided example file `.env.example` to a new file named `.env` in the root of the repository:
    ```bash
    cp .env.example .env
    ```
2.  **Edit `.env`:** Open the `.env` file and:
    *   **Set your `OPENAI_API_KEY`**: Replace `"YOUR_API_KEY_HERE"` with your actual OpenAI API key.
    *   (Optional) **Override default models**: You can also set `EMBEDDING_MODEL` and `CHAT_MODEL` in this file if you wish to use different models than the defaults. If these lines are commented out or not present, the application will use the default models.

    Example `.env` file content:
    ```
    # OpenAI API Key (required)
    OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    # OpenAI Model Names (optional, defaults will be used if not set)
    # EMBEDDING_MODEL="text-embedding-3-small"
    # CHAT_MODEL="gpt-3.5-turbo"
    ```

3.  **Git Integration:** The `.env` file is listed in `.gitignore`, so your local `.env` file (containing your API key) will not be committed to the Git repository.

The application will automatically load these variables from the `.env` file if it exists. You can also set these variables directly in your shell environment, which will take precedence over a `.env` file.

## Repository layout

- `app.py` – Flask server providing the `/api/chat` route.
- `index.html` – front‑end page with JavaScript for sending chat messages.
- `Description Deutsch`, `Description Französisch`, `Description Italienisch`, `Description English` – source documents in different languages.
- `available_models.py` – helper script to print the available OpenAI models.
- `static/` – images used by the front end.


