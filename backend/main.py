import os
import json
import time
import requests
from pathlib import Path
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import pyttsx3 
from fastapi.concurrency import run_in_threadpool
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from fastapi.middleware.cors import CORSMiddleware



# --- Configuration & Setup ---
load_dotenv()
app = FastAPI(title="eduX Course Generator API")

origins = [
    "http://localhost:3000",
    "http://172.18.104.181:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Google Gemini
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("GOOGLE_API_KEY not found.")
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel('models/gemini-pro-latest')

# Configure Pexels API Key
pexels_api_key = os.getenv("PEXELS_API_KEY")
if not pexels_api_key:
    raise ValueError("PEXELS_API_KEY not found.")

# Create directories to store media files
Path("audio_outputs").mkdir(exist_ok=True)
Path("image_outputs").mkdir(exist_ok=True)
Path("video_outputs").mkdir(exist_ok=True)

# Initialize the local TTS engine
try:
    tts_engine = pyttsx3.init()
except Exception as e:
    print(f"Could not initialize TTS engine: {e}")
    tts_engine = None


# --- Pydantic Models ---
class CourseRequest(BaseModel):
    prompt: str
    days: int = 30
    daily_commitment_minutes: int = 60


# --- AI Prompts ---
CURRICULUM_PROMPT = """
<role>
You are an expert curriculum designer and subject matter expert. Your task is to create a structured, day-by-day course outline based on a user's learning goal.
</role>
<instructions>
1.  Analyze the user's learning goal provided in the <user_prompt> tag.
2.  Determine the most logical, step-by-step progression to achieve that goal in the specified number of days.
3.  Generate a curriculum as a valid JSON object.
4.  The JSON object must have a single root key: "course_outline".
5.  The value of "course_outline" must be an array of JSON objects, one for each day.
6.  Each daily object must contain three keys: "day" (integer), "title" (a concise and engaging lesson title), and "description" (a one-sentence summary of the lesson).
7.  Do NOT output any text, explanation, or conversational filler before or after the JSON object. Your entire response must be only the JSON.
</instructions>
<user_prompt>
{user_prompt}
</user_prompt>
<course_duration>
{course_duration} days
</course_duration>
"""

LESSON_PROMPT = """
<role>
You are an expert content creator and teacher for a video course. Your task is to generate the complete content for a single video lesson based on the provided title and duration.
</role>
<instructions>
1.  Analyze the lesson title provided in the <lesson_title> tag.
2.  Generate the content as a valid JSON object.
3.  The JSON object must have three root keys: "video_script", "quiz", and "image_prompts".
4.  For "video_script": Write a detailed, engaging script as a single block of plain text. Use paragraphs separated by newlines (\\n). The script should be long enough for a {video_duration}-minute video. The tone must be friendly, encouraging, and educational.
5.  For "quiz": Create a {quiz_duration}-minute assessment as an array of multiple-choice question objects. Each object must have three keys: "question" (string), "options" (an array of 4 strings), and "correct_answer".
6.  For "image_prompts": Create an array of descriptive text prompts for an AI image generator.
7.  Do NOT output any conversational filler before or after the JSON.
</instructions>
<lesson_title>
{lesson_title}
</lesson_title>
"""


# --- Helper Functions ---
def generate_lesson_content(title: str, video_duration: int, quiz_duration: int):
    prompt_for_ai = LESSON_PROMPT.format(
        lesson_title=title, video_duration=video_duration, quiz_duration=quiz_duration)
    try:
        response = model.generate_content(prompt_for_ai)
        cleaned_json_string = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_json_string)
    except Exception as e:
        print(f"Error generating lesson for '{title}': {e}")
        return {"error": f"Failed to generate content for lesson: {title}"}

def generate_audio_for_script(script: any, day: int) -> str:
    if tts_engine is None:
        return "TTS engine not initialized."
    if not isinstance(script, str):
        print(f"Error for Day {day}: The provided script is not a valid string.")
        return "Audio generation failed due to invalid script format."
    try:
        file_path = f"audio_outputs/day_{day}_audio.mp3"
        print(f"Generating local audio for Day {day}...")
        tts_engine.save_to_file(script, file_path)
        tts_engine.runAndWait()
        print(f"Audio for Day {day} saved to {file_path}")
        return file_path
    except Exception as e:
        print(f"--- LOCAL TTS ERROR (Day {day}) --- \n {e} \n -----------------------------")
        return "Audio generation failed."

def generate_images_for_lesson(prompts: list, day: int) -> list[str]:
    image_paths = []
    day_folder = Path(f"image_outputs/day_{day}")
    day_folder.mkdir(exist_ok=True)
    
    if not prompts:
        return []

    # We will only use the first prompt to find one image per lesson
    first_prompt = prompts[0]
    
    api_url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": pexels_api_key}

    try:
        print(f"Searching for image for Day {day} via Pexels...")
        params = {"query": first_prompt, "per_page": 1}
        
        response = requests.get(api_url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data['photos']:
                image_url = data['photos'][0]['src']['large']
                image_data = requests.get(image_url).content
                file_path = day_folder / "image_0.jpeg"
                with open(file_path, "wb") as f:
                    f.write(image_data)
                image_paths.append(str(file_path))
            else:
                print(f"No image found on Pexels for prompt: '{first_prompt}'")
        else:
            print(f"--- PEXELS API ERROR --- \n Status: {response.status_code}, Body: {response.text}")

    except Exception as e:
        print(f"--- REQUESTS ERROR --- \n {e}")
            
    return image_paths

def assemble_video(audio_path: str, image_paths: list, day: int) -> str:
    if not audio_path or not image_paths or "failed" in audio_path:
        print(f"Skipping video assembly for Day {day}: Missing audio or image files.")
        return "Video assembly skipped."

    try:
        print(f"Assembling video for Day {day}...")
        audio_clip = AudioFileClip(audio_path)
        video_duration = audio_clip.duration
        
        # We will show our single image for the entire duration
        duration_per_image = video_duration / len(image_paths)
        
        image_clips = [ImageClip(path).set_duration(duration_per_image) for path in image_paths]
        
        final_clip = concatenate_videoclips(image_clips, method="compose")
        
        final_clip = final_clip.set_audio(audio_clip)
        
        output_path = Path(f"video_outputs/day_{day}_video.mp4")
        final_clip.write_videofile(str(output_path.resolve()), fps=24, codec='libx264', audio_codec='aac', audio_fps=44100)
        
        print(f"Video for Day {day} saved to {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"--- MOVIEPY ERROR (Day {day}) --- \n {e} \n -----------------------------")
        return "Video assembly failed."

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the eduX API!"}

@app.post("/generate-full-course")
async def generate_full_course(request: CourseRequest):
    
    def full_generation_blocking_task():
        try:
            curriculum_prompt_for_ai = CURRICULUM_PROMPT.format(
                user_prompt=request.prompt, course_duration=request.days)
            response = model.generate_content(curriculum_prompt_for_ai)
            cleaned_json_string = response.text.strip().replace("```json", "").replace("```", "")
            curriculum = json.loads(cleaned_json_string)
        except Exception as e:
            print(f"Failed to generate curriculum: {e}")
            return {"error": f"Failed to generate curriculum: {e}"}

        video_duration = int(request.daily_commitment_minutes * 0.8)
        quiz_duration = request.daily_commitment_minutes - video_duration
        
        course_outline = curriculum.get("course_outline", [])
        for day_plan in course_outline:
            lesson_title = day_plan.get("title")
            if lesson_title:
                lesson_content = generate_lesson_content(
                    lesson_title, video_duration, quiz_duration)
                day_plan["lesson_content"] = lesson_content
                
                audio_path = None
                image_paths = None

                script = lesson_content.get("video_script")
                if script:
                    audio_path = generate_audio_for_script(script, day_plan["day"])
                    day_plan["audio_file_path"] = audio_path

                image_prompts = lesson_content.get("image_prompts", [])
                if image_prompts:
                    image_paths = generate_images_for_lesson(image_prompts, day_plan["day"])
                    day_plan["image_file_paths"] = image_paths

                if audio_path and image_paths:
                    video_path = assemble_video(audio_path, image_paths, day_plan["day"])
                    day_plan["video_file_path"] = video_path
        
        return curriculum

    return await run_in_threadpool(full_generation_blocking_task)