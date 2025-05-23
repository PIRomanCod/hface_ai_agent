from langchain_core.tools import tool
from pathlib import Path
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


@tool
def audio_transcriber(audio: str) -> str:
    """Transcribes a local audio file using OpenAI Whisper API."""
    audio_path = Path(audio)
    if not audio_path.exists():
        return f"Error: File not found at {audio_path}"
    if not audio_path.is_file():
        return f"Error: {audio_path} is not a file"
    if audio_path.stat().st_size > 25 * 1024 * 1024:
        return "Error: Audio file is too large (max 25MB)"

    try:
        client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))    
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        
        return f"Extracted data from audio:\n\n{transcript.text}. You can use this to process answer."
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"