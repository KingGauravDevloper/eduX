# main.py
import os
import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# --- Configuration ---
# Set up the FastAPI app
app = FastAPI(
    title="EduX Course Generator API",
    description="An API to generate video courses from a user prompt."
)

# Configure the Google Generative AI model with the API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')


# --- Pydantic Models (for API request body) ---
# This defines the structure of the data we expect from the user
class CourseRequest(BaseModel):
    prompt: str
    days: int = 30 # Default to 30 days if not provided
    
    
# --- The Master Prompt for the AI ---
# This is the most important part. It's our instruction manual for the AI.
# We are asking it to act as an expert and return a structured JSON.
MASTER_PROMPT = """
You are an expert curriculum designer and subject matter expert.
Your task is to create a structured, day-by-day course outline based on a user's learning goal.
The user's prompt will be provided to you.
You MUST output the course curriculum as a valid JSON object.

The JSON object should have a single key "course_outline", which is an array of day objects.
Each day object in the array must contain:
1. "day": The day number (integer).
2. "title": A concise and engaging title for the day's lesson (string).
3. "description": A one-sentence summary of what the user will learn (string).

User's Learning Goal: "{user_prompt}"
Course Duration: {course_duration} days.

Generate the JSON curriculum now.
"""


# --- API Endpoints ---
@app.get("/")
def read_root():
    """A simple endpoint to check if the server is running."""
    return {"status": "ok", "message": "Welcome to the EduX API!"}


@app.post("/generate-curriculum")
def generate_curriculum(request: CourseRequest):
    """
    Generates a structured course curriculum from a user prompt.
    """
    # Format our master prompt with the user's specific request
    prompt_for_ai = MASTER_PROMPT.format(
        user_prompt=request.prompt,
        course_duration=request.days
    )
    
    try:
        # Make the API call to the Gemini model
        response = model.generate_content(prompt_for_ai)
        
        # The AI's response might include backticks and the word "json"
        # We need to clean that up to get a pure JSON string.
        cleaned_json_string = response.text.strip().replace("```json", "").replace("```", "")
        
        return {
            "message": "Curriculum generated successfully!",
            "raw_ai_response": cleaned_json_string
        }
        
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}