# check_models.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load the same .env file to get your API key
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")

genai.configure(api_key=api_key)

print("--- Available Models ---")
for m in genai.list_models():
  # We only care about models that support the 'generateContent' method
  if 'generateContent' in m.supported_generation_methods:
    print(m.name)
print("------------------------")