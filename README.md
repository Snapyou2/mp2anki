# mp2anki : Audio lesson summarizer and anki cards generator

This Python script automatically transcribes audio recordings of lessons (e.g., lectures, podcasts), generates summaries, and creates Anki flashcards for key vocabulary terms using the Google Gemini API and the FasterWhisper speech-to-text model.

## Features

- **Automatic Transcription:** Uses FasterWhisper to convert audio or video files to text.
- **Vocabulary Extraction and Anki Flashcard Generation:** Extracts key vocabulary terms from the Whisper transcript using the Gemini API and formats them as Anki flashcards that can be easily imported into Anki.
- **Lesson Summary Creation:**  Generates a comprehensive summary of the lesson content using the Gemini API.
- **Organized Output:** Saves Anki flashcards decks and summaries as separate files for easy access.

## Dependencies

- **Python 3.8 or higher**
- **google-generativeai:** For interacting with the Google Gemini API. Install with:
  ```bash
  pip install google-generativeai
  ```
  or preferably in a virtual python environment
- **FasterWhisper:** A fast and accurate speech-to-text model. Follow the installation instructions from the official repository:
  [https://github.com/SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- **ffmpeg:** Used by Whisper. Install on Debian-based systems with : 
  ```bash
  sudo apt update && sudo apt install ffmpeg
  ```

## Setup

1. **API key:**
   - Obtain a [Google AI Studio API key](https://aistudio.google.com/app/apikey).
   - Set the `API_KEY` variable in the script to your API key.
2. **Project ID:**
   - Find your Google Cloud project ID (on the same page as your API key in Google AI Studio)
   - Set the `PROJECT_ID` variable in the script.
3. **Main directory:**
   - Set `MAIN_DIR` to the directory where you want to store the audio files, transcripts, Anki flashcards, and summaries.
4. **FasterWhisper executable path:** 
   - Set `LOCATION` in the script to the path to your FasterWhisper executable (e.g., `/path/to/FasterWhisper/main`). 
5. **Audio or video files:**
   - Place your audio or video files in the `MAIN_DIR`.

## Usage

1. **Add your files in the MAIN_DIR**
   - It can be any video or audio format. Rename them accordingly to their content first. All media files in this directory will be processed. You can use child directories to store files between runs.
3. **Run the script:**
   ```bash
   python mp2anki.py
   ```
4. **Output:**
   - For each audio file, it will:
     - Transcribe the audio using Whisper.
     - Generate Anki flashcards and a lesson summary using the Gemini API.
     - Save the Anki flashcards to a file named `Anki_[media_filename].txt`.
     - Save the lesson summary and its key concepts to revise to a file named `Summary_key_concepts_[media_filename].md`. 

## Notes

- The script uses a prompt template to guide the Gemini API in generating the desired outputs. You can obviously customize this template if needed. If you do, please modify the markers that I used to split the API response in multiple files as they can change depending on your template.
- Sadly, errors can happen with the AI Studio API. It is relatively rare but it hopefully will be debugged in the future.
- Make sure you have configured your Google Cloud project and credentials correctly for the Gemini API.
- The accuracy of the transcription, the quality of the summaries and the relevance of Anki cards depend on the quality of the audio recording and the performance of the Whisper and Gemini models. Please check manually the cards before importing them into Anki.

## Example

If you have an audio file named `lesson1.mp3` in your `MAIN_DIR`, the script will create the following files:

- `Anki_lesson1.txt`, containing the Anki flashcards, that can be imported as a TXT file into Anki
- `Summary_key_concepts_lesson1.md`, containing the lesson summary and the key concepts of the lesson.
- `lesson1.txt` (containing the transcription created by whisper)

