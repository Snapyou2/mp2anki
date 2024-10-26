import os
import re
import json
import time
import google.generativeai as genai

# --- Configuration ---
MAIN_DIR = ""  # Where this script is and where you will put lessons files
LOCATION = "" # Your Faster-whisper model location
API_KEY = ""  # Google AI Studio API key
PROJECT_ID = ""  # When you create an API key
MODEL_NAME = "gemini-1.5-pro-exp-0827"  # You can change that for newer models

# Configure Google AI Platform
genai.configure(api_key=API_KEY)

# --- Prompt Template ---
PROMPT_TEMPLATE = """
I made this recording of a lesson and transcribed it with Whisper.

Please make a list of all the vocabulary terms that I need to revise and
understand for my first year of neurosciences. Present them as an Anki
flashcard list of the vocabulary terms with the explanation for each term
that I can import into Anki as a txt.

Also create a list of all the useful topics to revise in this lesson.

Then make a nice complete resume/summary of this lesson. Do NOT forget important topics.

Here is an example of the correct answer format (keep this exact format for the Anki list, without useless line breaks):

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

Here is the transcription text:

[insert transcription text from whisper here]
"""

# --- Functions ---


def transcribe_audio(audio_file_path):
    """Transcribes an audio file using Whisper."""
    transcript_file_path = os.path.splitext(audio_file_path)[0] + ".txt"
    try:
        whisper_command = f"{LOCATION} {audio_file_path} --output_format txt --language en > {transcript_file_path}"
        os.system(whisper_command)
        with open(transcript_file_path, "r") as f:
            transcript = f.read()

        # Remove unwanted information (timestamps and progress) using regex
        transcript = re.sub(r"\[.*?\]", "", transcript)
        transcript = re.sub(r"\]0;.*?audio seconds/s", "", transcript)
        transcript = re.sub(r"Transcription speed:.*", "", transcript)
        transcript = re.sub(r"Subtitles are written to.*", "", transcript)
        transcript = transcript.strip()
        return transcript
    except FileNotFoundError:
        print(f"Error: Whisper executable not found at {LOCATION}")
        return None
    except Exception as e:
        print(f"Error during Whisper transcription: {e}")
        return None


def extract_information(response):
    """Extracts Anki cards and summary+topics from the Gemini response."""
    if response and response.candidates:
        for candidate in response.candidates:
            # Prioritize accessing text content using different methods
            if hasattr(candidate, "content"):
                text = str(candidate.content)
            elif hasattr(candidate, "text"):
                text = str(candidate.text)
            elif hasattr(candidate, "output") and isinstance(candidate.output, str):
                try:
                    # Attempt to parse JSON-like output (if any)
                    data = json.loads(candidate.output)
                    if "candidates" in data and data["candidates"]:
                        text = data["candidates"][0].get("content", "")  # Get 'content' safely
                    else:
                        text = ""  # No usable content found in JSON
                except json.JSONDecodeError:
                    print("Warning: Could not parse candidate.output as JSON.")
                    text = ""
            else:
                print("Warning: Candidate object has no usable text attribute.")
                return None, None

            # Extract sections using markers (more robust to changes)
            anki_cards = extract_section(text, "## Anki Flashcard List:", "## Lesson Summary:")
            summary_and_topics = extract_section(text, "## Lesson Summary:", None)  # Extract to the end

            # Extract the title (assuming it's the first line before "## Anki Flashcard List:")
            title = text.split("## Anki Flashcard List:")[0].strip()

            # Prepend the title to the summary_and_topics
            summary_and_topics = f"# {title}\n\n{summary_and_topics}"

            # Remove content after the last "}" in summary_and_topics (if present)
            last_brace_index = summary_and_topics.rfind("}")
            if last_brace_index != -1:
                summary_and_topics = summary_and_topics[: last_brace_index + 1]

            # Replace \n with newline characters in all sections
            if anki_cards:
                anki_cards = anki_cards.replace("\\n", "\n").replace("*", "")
            if summary_and_topics:
                summary_and_topics = summary_and_topics.replace("\\n", "\n")

            return anki_cards, summary_and_topics
    return None, None


def extract_section(text, start_marker, end_marker):
    """Extracts a section of text between start and end markers."""
    start_index = text.find(start_marker)
    if start_index == -1:
        print(f"Warning: Start marker '{start_marker}' not found.")
        return None  # Or an empty string "" if you prefer

    start_index += len(start_marker)

    if end_marker:
        end_index = text.find(end_marker, start_index)
        if end_index == -1:
            print(f"Warning: End marker '{end_marker}' not found.")
            return text[start_index:].strip()
        else:
            return text[start_index:end_index].strip()
    else:
        return text[start_index:].strip()


def process_audio(audio_file):
    print(f"Processing: {audio_file}")
    audio_file_path = os.path.join(MAIN_DIR, audio_file)
    transcript_file_path = os.path.splitext(audio_file_path)[0] + ".txt"
    audio_file_base_name = os.path.splitext(audio_file)[0]

    # Check if transcript already exists
    if os.path.exists(transcript_file_path):
        print("Transcript file found. Skipping Whisper transcription.")
        with open(transcript_file_path, "r") as f:
            transcript = f.read()
    else:
        transcript = transcribe_audio(audio_file_path)  # Assuming you have this function defined
        if transcript is None:
            print(f"Skipping {audio_file} due to transcription error.")
            return

    prompt = PROMPT_TEMPLATE.replace("[insert transcription text from whisper here]", transcript)
    model = genai.GenerativeModel(MODEL_NAME)

    for attempt in range(1, 4):  # Retry up to 3 times
        try:
            print("Sending prompt to Gemini...")
            response = model.generate_content(prompt)
            print("Response received. Extracting information...")

            anki_cards, summary_and_topics = extract_information(response)  # Assuming you have this function defined

            if anki_cards is not None and summary_and_topics is not None:
                # Create output folder
                output_folder = os.path.join(MAIN_DIR, audio_file_base_name)
                os.makedirs(output_folder, exist_ok=True)

                # Save Anki cards
                anki_file_path = os.path.join(output_folder, f"Anki_{audio_file_base_name}.txt")
                with open(anki_file_path, "w") as f:
                    f.write(anki_cards)
                print(f"Anki cards saved to: {anki_file_path}")

                # Save summary and topics
                summary_topics_file_path = os.path.join(output_folder, f"Summary+Key_concepts_{audio_file_base_name}.md")
                with open(summary_topics_file_path, "w") as f:
                    f.write(summary_and_topics)
                print(f"Summary and key concepts saved to: {summary_topics_file_path}")

                # Save transcript (in the output folder)
                transcript_file_path = os.path.join(output_folder, f"{audio_file_base_name}_transcript.txt")
                with open(transcript_file_path, "w") as f:
                    f.write(transcript)
                print(f"Transcript saved to: {transcript_file_path}")

                print(f"Finished processing: {audio_file}\n")
                break  # Exit the loop after a successful attempt

            else:
                print("No usable information extracted from Gemini's response.")

        except Exception as e:
            print(f"API error (attempt {attempt}/3): {e}")
            if attempt < 3:
                time.sleep(30)  # Wait before retrying


# --- Main Execution ---
if __name__ == "__main__":
    for filename in os.listdir(MAIN_DIR):
        if filename.lower().endswith(
            (
                ".mp3",
                ".wav",
                ".mp4",
                ".m4a",
                ".aac",
                ".ogg",
                ".flac",
                ".webm",
                ".mkv",
                ".m4v",
            )
        ):
            process_audio(filename)
