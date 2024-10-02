import os
import re
import json
import google.generativeai as genai

# --- Configuration ---
MAIN_DIR = "path/to/your/main/directory" # Where this script is and where you will put lessons files
LOCATION = "path/to/your/FasterWhisper/script"
API_KEY = "your_api_key" # Google AI Studio API key
PROJECT_ID = "your_project_id" # When you create an API key
MODEL_NAME = "gemini-1.5-pro" # You can change that for newer models

# Configure Google AI Platform
genai.configure(api_key=API_KEY)

# --- Prompt Template ---
# Feel free to modify it if you want to
PROMPT_TEMPLATE = """
I made this recording of a lesson and transcribed it with Whisper.

Please make a list of all the vocabulary terms that I need to revise and 
understand for my first year of neurosciences. Present them as an Anki 
flashcard list of the vocabulary terms with the explanation for each term 
that I can import into Anki as a txt.

Also create a list of all the useful topics to revise in this lesson.

Then make a nice complete resume/summary of this lesson. Do NOT forget important topics.

Here is an nice example of correct answer (keep the exact same format for 
the Anki list, without useless line breaks) :

## Anki Flashcard List:
White matter: Brain tissue composed primarily of myelinated axons, responsible for fast transmission of information.
Gray matter: Brain tissue composed primarily of neuronal cell bodies, responsible for information processing.
... (rest of the example Anki list) ...

## Lesson Summary:
This lesson delves into the intricate microarchitecture of the human brain... 
... (rest of the example summary) ...

## Useful Topics to Revise:
* **Microarchitecture of the human brain:**
    * White matter vs. gray matter
    ... (rest of the example topics) ...

Here is the transcription text :

[insert transcription text from whisper here]
"""

# --- Functions ---

def transcribe_audio(audio_file_path):
    """Transcribes an audio file using Whisper.

    Args:
        audio_file_path: The path to the audio file.

    Returns:
        The transcribed text as a string.
    """
    transcript_file_path = os.path.splitext(audio_file_path)[0] + ".txt"
    whisper_command = (
        f"{LOCATION} {audio_file_path} "
        f"--output_format txt --language en > {transcript_file_path}"
    )
    os.system(whisper_command)
    with open(transcript_file_path, "r") as f:
        return f.read()

def extract_anki_cards(response_text):
    """Extracts the Anki flashcard list from the Gemini response.

    Args:
        response_text: The full text of the Gemini response.

    Returns:
        The Anki flashcard list as a string.
    """
    start_marker = "## Anki Flashcard List:"
    end_marker = "## Lesson Summary:"
    start_index = response_text.find(start_marker) + len(start_marker)
    end_index = response_text.find(end_marker)
    anki_text = response_text[start_index:end_index].strip()
    # Remove bold markers and extra whitespace
    anki_text = re.sub(r'\*\*(.*?)\*\*', r'\1', anki_text) 
    return anki_text

def extract_summary(response_text):
    """Extracts the lesson summary from the Gemini response.

    Args:
        response_text: The full text of the Gemini response.

    Returns:
        The lesson summary as a string.
    """
    start_marker = "## Lesson Summary:"
    start_index = response_text.find(start_marker) + len(start_marker)
    return response_text[start_index:].strip()

def process_audio(audio_file):
    """Processes a single audio file: transcribes, generates Gemini response, 
       and saves outputs.

    Args:
        audio_file: The name of the audio file. 
    """
    print(f"Processing: {audio_file}")
    audio_file_path = os.path.join(MAIN_DIR, audio_file)
    transcript = transcribe_audio(audio_file_path)
    print("Whisper transcript:\n---\n" + transcript + "\n---")

    prompt = PROMPT_TEMPLATE.replace("[insert transcription text from whisper here]", transcript)
    model = genai.GenerativeModel(MODEL_NAME)

    # Retry mechanism for API calls
    max_retries = 3  # Maximum number of retries
    retry_delay = 5  # Seconds to wait between retries

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            break  # Exit the loop if the API call is successful
        except ResourceExhausted as e:
            print(f"API call failed with ResourceExhausted error: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Maximum retries reached. Skipping this file.")
                return  # Skip the rest of the processing for this file

    anki_cards = extract_anki_cards(response.text)
    summary = extract_summary(response.text)

    # Save Anki cards
    anki_file = "Anki_" + os.path.splitext(audio_file)[0] + ".txt"
    anki_file_path = os.path.join(MAIN_DIR, anki_file) 
    with open(anki_file_path, "w") as f:
        f.write(anki_cards)
    print(f"Anki cards saved to: {anki_file_path}")

    # Save summary
    summary_file = "Summary_key_concepts_" + os.path.splitext(audio_file)[0] + ".md"
    summary_file_path = os.path.join(MAIN_DIR, summary_file)
    with open(summary_file_path, "w") as f:
        f.write(summary)
    print(f"Summary saved to: {summary_file_path}")
   
    # Print Gemini response
    print("\n--- Gemini API Response ---\n")
    print(response.text)
    print("\n--- End of Gemini API Response ---\n")
   
    print(f"Finished processing: {audio_file}\n")

# --- Main Execution ---
if __name__ == "__main__":
    for filename in os.listdir(MAIN_DIR):
        # Check if the file has a supported extension (hardcoded common media formats)
        if (filename.lower().endswith((".mp3", ".wav", ".mp4", ".m4a", ".aac", ".ogg", ".flac", ".webm", ".mkv", ".m4v"))):
            process_audio(filename)
