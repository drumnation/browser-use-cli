import google.generativeai as genai
import os
from dotenv import load_dotenv, find_dotenv

# Force reload of environment variables
load_dotenv(find_dotenv(), override=True)

api_key = os.environ.get("GOOGLE_API_KEY")
model_name = os.environ.get("GOOGLE_API_MODEL")

if not api_key or not model_name:
    raise ValueError("Missing required environment variables: GOOGLE_API_KEY or GOOGLE_API_MODEL")

print(f"Using model: {model_name}")
genai.configure(api_key=api_key, transport="rest")

# List all available models
print("\nAvailable models:")
for m in genai.list_models():
    print(f"- {m.name}")

# Check that the model exists in the client
found_model = False
for m in genai.list_models():
    model_id = m.name.replace("models/", "")
    if model_id == model_name:
        found_model = True
        print(f"\nFound model: {m.name}")
        break

if not found_model:
    print("\nAvailable model IDs:")
    for m in genai.list_models():
        print(f"- {m.name.replace('models/', '')}")

assert found_model, f"Model not found: {model_name}"

# Load the model
model = genai.GenerativeModel(model_name)

# Perform a simple generation task
try:
    response = model.generate_content("Hello, I'm testing the Gemini API connection. Please respond with a short greeting.")
    print(f"\nResponse: {response.text}")
except Exception as e:
    print(f"\nError generating content: {e}")
    raise 