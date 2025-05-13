#%%
import os
from openai import OpenAI

def translate_files_to_language(source_folder: str,
                                target_folder: str,
                                language: str,
                                openai_api_key: str,
                                model_name: str = "gpt-4"):
    """
    Translates all .txt files in source_folder to a specified language using OpenAI GPT API
    and saves the translated files in target_folder.

    :param source_folder: Path to the folder containing .txt files.
    :param target_folder: Path to the folder where translated .txt files will be saved.
    :param language: The target language (e.g., "Spanish", "French", etc.).
    :param openai_api_key: Your OpenAI API key.
    :param model_name: The model to use, e.g., 'gpt-4' or 'gpt-3.5-turbo'.
    """
    # Initialize OpenAI client
    client = OpenAI(api_key=openai_api_key)

    # Ensure the target folder exists
    os.makedirs(target_folder, exist_ok=True)

    # Process each .txt file in the source folder
    for filename in os.listdir(source_folder):
        if filename.endswith(".txt"):
            source_path = os.path.join(source_folder, filename)
            target_path = os.path.join(target_folder, filename)

            # Read original content
            with open(source_path, "r", encoding="utf-8") as f:
                original_text = f.read()

            # Request translation via OpenAI API
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful translator."},
                        {"role": "user", "content": f"Translate the following text to {language}:\n\n{original_text}"}
                    ],
                    temperature=0
                )

                # Extract translated text
                translated_text = response.choices[0].message.content

            except Exception as e:
                print(f"Error translating file {filename}: {e}")
                continue

            # Save translation
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(translated_text)

            print(f"Translated {filename} -> {target_path}")

    print("Translation complete!")


if __name__ == "__main__":
    YOUR_OPENAI_API_KEY =  "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"

    SOURCE_FOLDER = "Description Deutsch"
    TARGET_FOLDER = "Description Französisch"
    TARGET_LANGUAGE = "French"
    MODEL_NAME = "gpt-4.5-preview"

    translate_files_to_language(
        source_folder=SOURCE_FOLDER,
        target_folder=TARGET_FOLDER,
        language=TARGET_LANGUAGE,
        openai_api_key=YOUR_OPENAI_API_KEY,
        model_name=MODEL_NAME
    )
# %%
