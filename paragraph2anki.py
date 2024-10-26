import os
import re
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv
from mp2anki import PROMPT_TEMPLATE, extract_information

load_dotenv()

# --- Configuration ---
MAIN_DIR = os.getenv("MAIN_DIR")  # Where this script is and where you will put lessons files
LOCATION = os.getenv("LOCATION") # Your Faster-whisper model location
API_KEY = os.getenv("API_KEY")  # Google AI Studio API key
PROJECT_ID = os.getenv("PROJECT_ID")  # When you create an API key
MODEL_NAME = os.getenv("MODEL_NAME")  # You can change that for newer models
TEXT_FILENAME = os.getenv("TEXT_FILENAME")  # The name of the textfile with the paragraph

def test_implementaton(paragraph : str):
    prompt = PROMPT_TEMPLATE.replace("[insert transcription text from whisper here]", paragraph)
    model = genai.GenerativeModel(MODEL_NAME)

    for attempt in range(1, 4):  # Retry up to 3 times
        try:
            print("Sending prompt to Gemini...")
            response = model.generate_content(prompt)
            print("Response received. Extracting information...")
            subdir = TEXT_FILENAME.split(".")[0]

            anki_cards, summary_and_topics = extract_information(response)  # Assuming you have this function defined

            if anki_cards is not None and summary_and_topics is not None:
                # Create output folder
                output_folder = os.path.join(MAIN_DIR, subdir)
                os.makedirs(output_folder, exist_ok=True)

                # Save Anki cards
                anki_file_path = os.path.join(output_folder, f"Anki_{subdir}.txt")
                with open(anki_file_path, "w") as f:
                    f.write(anki_cards)
                print(f"Anki cards saved to: {anki_file_path}")

                # Save summary and topics
                summary_topics_file_path = os.path.join(output_folder, f"Summary+Key_concepts_{subdir}.md")
                with open(summary_topics_file_path, "w") as f:
                    f.write(summary_and_topics)
                print(f"Summary and key concepts saved to: {summary_topics_file_path}")

                # Save transcript (in the output folder)
                transcript_file_path = os.path.join(output_folder, f"{subdir}_transcript.txt")
                with open(transcript_file_path, "w") as f:
                    f.write(paragraph)
                print(f"Transcript saved to: {transcript_file_path}")

                print(f"Finished processing:\n")
                break  # Exit the loop after a successful attempt

            else:
                print("No usable information extracted from Gemini's response.")

        except Exception as e:
            print(f"API error (attempt {attempt}/3): {e}")
            if attempt < 3:
                time.sleep(30)  # Wait before retrying
                
                
if __name__ == "__main__":
    with open(TEXT_FILENAME, "r") as f:
        paragraph = f.read()
        
    try:    
        test_implementaton(paragraph)
    
    except Exception as e:
        print(f"Error: {e}")
    