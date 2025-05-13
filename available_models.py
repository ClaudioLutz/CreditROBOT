#%%
import openai

#openai.api_key = "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"

openai.api_key = "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"

try:
    models = openai.models.list()
    print("Available models:")
    for model in models.data:
        print(model.id)
except Exception as e:
    print(f"Error fetching models: {e}")

# %%
